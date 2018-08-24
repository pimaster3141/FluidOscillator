/*
 * UART.c (2.0.1)
 *
 *  Created on: Aug 7, 2015
 *      Author: jasoyang
 *
 *	1.1 	6/15/16 	- Added generic receive action.
 *	1.2 	6/16/16 	- changed assuming 15.73MHz SMCLK
 *	1.3 	6/17/16 	- Removed Receive Buffers.
 *	1.4 	6/18/16 	- Added Pause in Init for stabilization
 *	2.0		11/20/16	- Generic for MSP430X devices
 *						- UCSI instance defined by #define
 *	2.0.1 	11/27/16	- Ported to MSP430FR5738 SPECIFIC - NON GENERIC
 */

#include <msp430fr5738.h>
#include "UART.h"

static volatile unsigned char UARTTXBuffer[UART_TX_BUFFER_SIZE];		// structure to hold transmit UART data (circular buffer)
static volatile unsigned char UARTTXBufferSendoutPointer = 0;	// pointer to next char to be sent out
static volatile unsigned char UARTTXBufferEndPointer = 0;		// pointer to first empty slot in buffer
static volatile unsigned char CTSRTS = 0;

#pragma vector=USCI_A0_VECTOR		//UART interrupt
__interrupt void UART_ISR(void)
{
	switch(UCA0IV)
	{
		case 0:		// no interrupt
			break;

		case 2:		// RX interupt
			UARTReceiveAction(UCA0RXBUF);   // call operation on byte
			break;
		case 4:	    // TX interrupt
			UCA0TXBUF = UARTTXBuffer[UARTTXBufferSendoutPointer];
			UARTTXBufferSendoutPointer++;
			if(UARTTXBufferSendoutPointer == UART_TX_BUFFER_SIZE)
				UARTTXBufferSendoutPointer = 0;
			if(UARTTXBufferSendoutPointer == UARTTXBufferEndPointer)
				UCA0IE &= ~UCTXIE;
			break;

		default:	// WTF...
			break;
	}
}


void UARTSetup(void)
{
	// Setup UART, 8N1 115200 baud, even from 20MHz
	UCA0CTLW0 |=  UCSSEL_2 + UCSWRST;	// CLK = SMCLK(DCO)
	UCA0CTLW1 = 1;

	UCA0BRW = 10;
	UCA0MCTLW = 0xAD00 + 0xD0 + UCOS16;

//    UCA0BRW = 8;
//    UCA0MCTLW = 0XADD0 + UCOS16;


	P2DIR|= BIT0;
	P2DIR &= ~(BIT1);
	P2REN |= BIT1;
	P2OUT |= BIT1;

	P2SEL1 |= BIT0;
	P2SEL1 |= BIT1;

	UCA0CTL1 &= ~UCSWRST;			// init uart

	__bis_SR_register(GIE);

	UCA0IE |= UCRXIE;				// Enable interrupts
}

void UARTSendByte(char byte)
{
	UARTTXBuffer[UARTTXBufferEndPointer] = byte;
	UARTTXBufferEndPointer++;
	if(UARTTXBufferEndPointer == UART_TX_BUFFER_SIZE)
		UARTTXBufferEndPointer = 0;
	if(!(P2IES & BIT2))
		UCA0IE |= UCTXIE;
}

void UARTSendArray(char *TxArray, char ArrayLength)
{
	while(ArrayLength--)
	{
		UARTTXBuffer[UARTTXBufferEndPointer] = *TxArray;
		TxArray++;
		UARTTXBufferEndPointer++;
		if(UARTTXBufferEndPointer == UART_TX_BUFFER_SIZE)
			UARTTXBufferEndPointer = 0;
	}
	if(!(P2IES & BIT2))
		UCA0IE |= UCTXIE;
	return;
}

void UARTSendCRLF(void)
{
	UARTTXBuffer[UARTTXBufferEndPointer] = 0x0D;
	UARTTXBufferEndPointer++;
	if(UARTTXBufferEndPointer == UART_TX_BUFFER_SIZE)
		UARTTXBufferEndPointer = 0;

	UARTTXBuffer[UARTTXBufferEndPointer] = 0x0A;
	UARTTXBufferEndPointer++;
	if(UARTTXBufferEndPointer == UART_TX_BUFFER_SIZE)
		UARTTXBufferEndPointer = 0;
	if(!(P2IES & BIT2))
		UCA0IE |= UCTXIE;
	return;
}

void UARTSendIntArray(int *data, char length)
{
	int i;
	for (i = 0; i < length; i++)
	{
		int current = data[i];
		char lowbyte = (char) (current & 0x00FF);
		char highbyte = (char) ((current >> 8) & 0x00FF);
		UARTSendByte(highbyte);
		UARTSendByte(lowbyte);
	}
	return;
}

void UARTSendByteBlocking(char data)
{
    UCA0IE &= ~UCTXIE;
    while(UCA0STATW & UCBUSY);
    UCA0TXBUF = data;
}
