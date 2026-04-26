#include "ringbuffer.h"
#include <stdlib.h>
#include <string.h>

typedef struct ringbuffer_s{
    void   *buffer;
    size_t  capacity;
    size_t  elem_size;
    size_t  head;
    size_t  tail;
    bool    full;
} ringbuffer_s;

static void advance_pointer(ringbuffer_t rb)
{
    if (rb->full) {
        rb->tail = (rb->tail + 1) % rb->capacity;
    }

    rb->head = (rb->head + 1) % rb->capacity;
    rb->full = (rb->head == rb->tail);
}

static void retreat_pointer(ringbuffer_t rb)
{
    rb->full = false;
    rb->tail = (rb->tail + 1) % rb->capacity;
}

ringbuffer_t ringbuffer_create(size_t capacity, size_t elem_size)
{
    if (capacity == 0 || elem_size == 0)
        return NULL;

    ringbuffer_t rb = malloc(sizeof(ringbuffer_s));
    if (!rb)
        return NULL;

    rb->buffer = malloc(capacity * elem_size);
    if (!rb->buffer) {
        free(rb);
        return NULL;
    }

    rb->capacity  = capacity;
    rb->elem_size = elem_size;
    rb->head = 0;
    rb->tail = 0;
    rb->full = false;

    return rb;
}

void ringbuffer_destroy(ringbuffer_t rb)
{
    if (!rb) return;

    free(rb->buffer);
    free(rb);
}

bool ringbuffer_push(ringbuffer_t rb, const void *item)
{
    if (!rb || !item)
        return false;

    memcpy((char*)rb->buffer + (rb->head * rb->elem_size),
           item,
           rb->elem_size);

    advance_pointer(rb);
    return true;
}

bool ringbuffer_pop(ringbuffer_t rb, void *item)
{
    if (!rb || !item || ringbuffer_is_empty(rb))
        return false;

    memcpy(item,
           (char*)rb->buffer + (rb->tail * rb->elem_size),
           rb->elem_size);

    retreat_pointer(rb);
    return true;
}

bool ringbuffer_is_empty(const ringbuffer_t rb)
{
    return (!rb->full && (rb->head == rb->tail));
}

bool ringbuffer_is_full(const ringbuffer_t rb)
{
    return rb->full;
}

size_t ringbuffer_size(const ringbuffer_t rb)
{
    if (rb->full)
        return rb->capacity;

    if (rb->head >= rb->tail)
        return rb->head - rb->tail;

    return rb->capacity + rb->head - rb->tail;
}
