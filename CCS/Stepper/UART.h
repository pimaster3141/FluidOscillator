/*
 * UART.h (2.0)
 *
 *  Created on: Aug 7, 2015
 *      Author: jasoyang
 *
 *	1.1 6/15/16 	- Added generic receive action. 
 *	1.2 6/17/16 	- Removed Recieve Buffers.
 *					- Renamed Methods
 *	2.0	11/20/16	- Generic for MSP430X devices
 *					- UCSI instance defined by #define
 */

#ifndef UART_H_
#define UART_H_

#define UART_TX_BUFFER_SIZE 50u
// #define UART_RX_BUFFER_SIZE 50u


void UARTSetup(void);
void UARTSendByte(char byte);
void UARTSendArray(char *TxArray, char ArrayLengh);
void UARTSendCRLF(void);
// void clearUARTRXBuffer(void);
void UARTSendIntArray(int *data, char length);
void UARTReceiveAction(unsigned char byte);
void UARTSendByteBlocking(char data);

#endif /* UART_H_ */
