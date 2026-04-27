#ifndef RINGBUFFER_H
#define RINGBUFFER_H

#include <stddef.h>
#include <stdbool.h>

typedef struct ringbuffer_s* ringbuffer_t;

/* Opretter ringbuffer og returnerer pointer (NULL ved fejl) */
ringbuffer_t ringbuffer_create(size_t capacity, size_t elem_size);

/* Frigiver buffer + struct */
void ringbuffer_destroy(ringbuffer_t rb);

bool ringbuffer_push(ringbuffer_t rb, const void *item);
bool ringbuffer_pop(ringbuffer_t rb, void *item);

bool   ringbuffer_is_empty(const ringbuffer_t rb);
bool   ringbuffer_is_full(const ringbuffer_t rb);
size_t ringbuffer_size(const ringbuffer_t rb);

#endif
