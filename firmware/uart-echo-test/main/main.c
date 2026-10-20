/* SPDX-License-Identifier: MIT */
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include "driver/uart.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
/* UART0 line echo test for the QEMU serial console */
void app_main(void) {
    uart_driver_install(UART_NUM_0, 1024, 0, 0, NULL, 0);
    printf("uart-echo-test ready: type a line\n");
    char line[256]; int n = 0; uint8_t c; int count = 0;
    while (1) {
        if (uart_read_bytes(UART_NUM_0, &c, 1, pdMS_TO_TICKS(1000)) == 1) {
            if (c == '\r' || c == '\n') {
                if (n) { line[n] = 0; for (int i = 0; i < n; i++) line[i] = toupper((int)line[i]);
                         printf("ECHO[%d]: %s (len=%d)\n", ++count, line, n); n = 0; }
            } else if (n < 255) line[n++] = c;
        }
    }
}
