#define _GNU_SOURCE
#include <fcntl.h>
#include <sched.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/stat.h>
#include <unistd.h>

struct control_page {
    _Atomic uint32_t ready;          /* 0 */
    _Atomic uint32_t mode;           /* 4 */
    _Atomic uint32_t target_cpu;     /* 8 */
    _Atomic uint32_t go;             /* 12 */
    _Atomic uint32_t done;           /* 16 */
    _Atomic uint32_t stop;           /* 20 */
    _Atomic uint32_t observed_cpu;   /* 24 */
    _Atomic uint32_t touched;        /* 28 */
    _Atomic uint32_t error;          /* 32 */
    _Atomic uint32_t page_index;     /* 36 */
    uint32_t guard_index;            /* 40 */
    uint32_t safe_start;             /* 44 */
    uint32_t safe_len;               /* 48 */
    uint32_t guard_cpu;              /* 52 */
    uint64_t region_addr;            /* 56 */
    uint64_t page_size;              /* 64 */
    _Atomic uint32_t discard_start;  /* 72 */
    _Atomic uint32_t discard_len;    /* 76 */
};

enum {
    MODE_TOUCH = 2,
    MODE_DISCARD = 3,
};

enum {
    ERR_CPU = 1,
    ERR_MODE = 2,
    ERR_INDEX_RANGE = 3,
    ERR_GUARD_RETOUCH = 4,
    ERR_DUPLICATE_TOUCH = 5,
    ERR_DISCARD_RANGE = 6,
    ERR_MADVISE = 7,
};

static inline void cpu_relax(void) {
#if defined(__x86_64__) || defined(__i386__)
    __asm__ __volatile__("pause" ::: "memory");
#else
    atomic_signal_fence(memory_order_seq_cst);
#endif
}

static void touch_page(unsigned char *region, long page_size, uint32_t index) {
    region[(size_t)index * (size_t)page_size] =
        (unsigned char)((index + 1U) & 0xffU);
}

static int choose_safe_span(
    uintptr_t region_addr,
    uint32_t max_pages,
    uint32_t safe_len,
    uint32_t *safe_start
) {
    const uint32_t pte_entries = 512U;
    uintptr_t base_page = region_addr >> 12;

    if (safe_len >= pte_entries || safe_len + 1U > max_pages)
        return -1;

    for (uint32_t start = 0; start + safe_len <= max_pages; ++start) {
        uint32_t pte_index =
            (uint32_t)((base_page + (uintptr_t)start) & 511U);
        if (pte_index + safe_len <= pte_entries) {
            *safe_start = start;
            return 0;
        }
    }
    return -1;
}

int main(int argc, char **argv) {
    const char *shared_path = NULL;
    uint32_t max_pages = 1024U;
    uint32_t safe_len = 192U;

    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--shared") && i + 1 < argc) {
            shared_path = argv[++i];
        } else if (!strcmp(argv[i], "--max-pages") && i + 1 < argc) {
            long value = strtol(argv[++i], NULL, 10);
            if (value < 256 || value > 65536)
                return 2;
            max_pages = (uint32_t)value;
        } else if (!strcmp(argv[i], "--safe-len") && i + 1 < argc) {
            long value = strtol(argv[++i], NULL, 10);
            if (value < 160 || value >= 512)
                return 2;
            safe_len = (uint32_t)value;
        } else {
            return 2;
        }
    }

    if (!shared_path)
        return 2;

    if (prctl(PR_SET_NAME, "frlq6", 0, 0, 0) != 0)
        return 2;

    long page_size = sysconf(_SC_PAGESIZE);
    if (page_size != 4096)
        return 2;

    int sfd = open(shared_path, O_RDWR | O_CLOEXEC);
    if (sfd < 0)
        return 2;

    struct control_page *ctl = mmap(
        NULL,
        (size_t)page_size,
        PROT_READ | PROT_WRITE,
        MAP_SHARED,
        sfd,
        0
    );
    if (ctl == MAP_FAILED)
        return 2;

    size_t region_size = (size_t)max_pages * (size_t)page_size;
    unsigned char *region = mmap(
        NULL,
        region_size,
        PROT_READ | PROT_WRITE,
        MAP_PRIVATE | MAP_ANONYMOUS,
        -1,
        0
    );
    if (region == MAP_FAILED)
        return 2;

#ifdef MADV_NOHUGEPAGE
    if (madvise(region, region_size, MADV_NOHUGEPAGE) != 0)
        return 2;
#endif

    uint32_t safe_start = 0;
    if (choose_safe_span(
            (uintptr_t)region,
            max_pages,
            safe_len,
            &safe_start
        ) != 0)
        return 2;

    unsigned char *used = calloc((size_t)max_pages, 1);
    if (!used)
        return 2;

    uint32_t guard_index = safe_start;

    /*
     * Allocate the PTE table on the preparation CPU. All later measured
     * pages stay inside this same PTE table.
     */
    int guard_cpu = sched_getcpu();
    touch_page(region, page_size, guard_index);
    used[guard_index] = 1;

    ctl->guard_index = guard_index;
    ctl->safe_start = safe_start;
    ctl->safe_len = safe_len;
    ctl->guard_cpu = (uint32_t)guard_cpu;
    ctl->region_addr = (uint64_t)(uintptr_t)region;
    ctl->page_size = (uint64_t)page_size;

    atomic_store_explicit(&ctl->observed_cpu, (uint32_t)guard_cpu, memory_order_release);
    atomic_store_explicit(&ctl->touched, 0, memory_order_release);
    atomic_store_explicit(&ctl->error, 0, memory_order_release);
    atomic_store_explicit(&ctl->ready, 1, memory_order_release);

    while (!atomic_load_explicit(&ctl->stop, memory_order_acquire)) {
        if (!atomic_load_explicit(&ctl->go, memory_order_acquire)) {
            cpu_relax();
            continue;
        }

        uint32_t mode = atomic_load_explicit(&ctl->mode, memory_order_acquire);
        uint32_t target_cpu = atomic_load_explicit(&ctl->target_cpu, memory_order_acquire);
        int seen = sched_getcpu();
        uint32_t error = 0;

        if (seen != (int)target_cpu) {
            error = ERR_CPU;
        } else if (mode == MODE_TOUCH) {
            uint32_t index =
                atomic_load_explicit(&ctl->page_index, memory_order_acquire);

            if (
                index < safe_start ||
                index >= safe_start + safe_len ||
                index >= max_pages
            ) {
                error = ERR_INDEX_RANGE;
            } else if (index == guard_index) {
                error = ERR_GUARD_RETOUCH;
            } else if (used[index]) {
                error = ERR_DUPLICATE_TOUCH;
            } else {
                touch_page(region, page_size, index);
                used[index] = 1;
                uint32_t touched =
                    atomic_load_explicit(&ctl->touched, memory_order_relaxed) + 1U;
                atomic_store_explicit(&ctl->touched, touched, memory_order_release);
            }
        } else if (mode == MODE_DISCARD) {
            uint32_t start =
                atomic_load_explicit(&ctl->discard_start, memory_order_acquire);
            uint32_t len =
                atomic_load_explicit(&ctl->discard_len, memory_order_acquire);

            if (
                len == 0 ||
                start < safe_start ||
                start + len > safe_start + safe_len ||
                start + len > max_pages ||
                start <= guard_index && guard_index < start + len
            ) {
                error = ERR_DISCARD_RANGE;
            } else {
                for (uint32_t i = start; i < start + len; ++i) {
                    if (!used[i]) {
                        error = ERR_DISCARD_RANGE;
                        break;
                    }
                }
                if (!error && madvise(
                        region + ((size_t)start * (size_t)page_size),
                        (size_t)len * (size_t)page_size,
                        MADV_DONTNEED
                    ) != 0) {
                    error = ERR_MADVISE;
                }
            }
        } else {
            error = ERR_MODE;
        }

        atomic_store_explicit(&ctl->observed_cpu, (uint32_t)seen, memory_order_release);
        atomic_store_explicit(&ctl->error, error, memory_order_release);
        atomic_store_explicit(&ctl->done, 1, memory_order_release);
        atomic_store_explicit(&ctl->go, 0, memory_order_release);
    }

    free(used);
    munmap(region, region_size);
    munmap(ctl, (size_t)page_size);
    close(sfd);
    return 0;
}
