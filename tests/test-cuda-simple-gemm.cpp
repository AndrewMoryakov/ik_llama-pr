#include "ggml.h"
#include "ggml-alloc.h"
#include "ggml-backend.h"

#ifdef GGML_USE_CUDA
#include "ggml-cuda.h"
#endif

#include <array>
#include <cmath>
#include <cstdio>
#include <vector>

static bool check(ggml_backend_t backend, ggml_type type, bool transpose) {
    constexpr int width = 1024;
    constexpr int rows = 2;
    ggml_context * ctx = ggml_init({ 64 * 1024, nullptr, true });
    auto * a = ggml_new_tensor_2d(ctx, type, width, rows);
    auto * storage = transpose ? ggml_new_tensor_2d(ctx, GGML_TYPE_F32, rows, width)
                               : ggml_new_tensor_2d(ctx, GGML_TYPE_F32, width + 1, rows);
    auto * b = transpose ? ggml_transpose(ctx, storage)
                        : ggml_view_2d(ctx, storage, width, rows, storage->nb[1], sizeof(float));
    if (transpose && ggml_backend_is_cpu(backend)) {
        b = ggml_cont(ctx, b);
    }
    auto * out = ggml_mul_mat(ctx, a, b);
    auto * graph = ggml_new_graph_custom(ctx, 16, false);
    ggml_build_forward_expand(graph, out);
    auto * buffer = ggml_backend_alloc_ctx_tensors(ctx, backend);
    if (!buffer) {
        ggml_free(ctx);
        return false;
    }

    std::vector<uint16_t> weights(rows * width);
    std::vector<float> inputs(ggml_nelements(storage), 0);
    std::array<float, rows * rows> expected{};
    for (int j = 0; j < rows; ++j) {
        for (int k = 0; k < width; ++k) {
            const float weight = float((k + 3*j) % 5 - 2);
            weights[j*width + k] = type == GGML_TYPE_F16 ? ggml_fp32_to_fp16(weight) : ggml_fp32_to_bf16(weight).bits;
            for (int i = 0; i < rows; ++i) {
                const float input = float((2*k + i) % 7 - 3);
                const int offset = transpose ? k*rows + i : i*(width + 1) + k + 1;
                inputs[offset] = input;
                expected[i*rows + j] += weight * input;
            }
        }
    }
    ggml_backend_tensor_set(a, weights.data(), 0, ggml_nbytes(a));
    ggml_backend_tensor_set(storage, inputs.data(), 0, ggml_nbytes(storage));
    std::array<float, rows * rows> actual{};
    const bool computed = ggml_backend_graph_compute(backend, graph) == GGML_STATUS_SUCCESS;
    bool ok = computed;
    if (computed) {
        ggml_backend_tensor_get(out, actual.data(), 0, ggml_nbytes(out));
        for (int i = 0; i < rows * rows; ++i) {
            ok = ok && std::abs(actual[i] - expected[i]) < 0.01f;
        }
    }
    if (!ok) {
        std::fprintf(stderr, "mul_mat failed on %s with %s weights and %s F32 input\n",
                ggml_backend_name(backend), ggml_type_name(type), transpose ? "transposed" : "misaligned");
    }
    ggml_backend_buffer_free(buffer);
    ggml_free(ctx);
    return ok;
}

int main() {
    std::array<ggml_backend_t, 2> backends{ggml_backend_cpu_init(), nullptr};
#ifdef GGML_USE_CUDA
    if (ggml_backend_cuda_get_device_count() > 0) {
        backends[1] = ggml_backend_cuda_init(0, nullptr, nullptr);
        if (!backends[1]) {
            ggml_backend_free(backends[0]);
            return 1;
        }
    }
#endif
    const bool run_cuda = backends[1] != nullptr;
    bool ok = true;
    for (auto * backend : backends) {
        if (!backend) {
            continue;
        }
        for (auto type : {GGML_TYPE_F16, GGML_TYPE_BF16}) {
            ok = check(backend, type, true) && ok;
            ok = check(backend, type, false) && ok;
        }
        ggml_backend_free(backend);
    }
    if (!run_cuda) {
        std::puts("CUDA unavailable; checked CPU reference cases only.");
    }
    return ok ? 0 : 1;
}
