#include <msp430.h> 
#include "UART.h"

/**
 * main.c
 * DCO_clk is 20MHz
 */

#define DELAY_LOOP_COUNT 800
#define PWM_FREQ 20000
#define PACKET_HEADER 0XAA
#define MOTOR_HEADER 0XBB
#define PULSE_CMD 0XCC
#define STATUS_REQ 0XDD
#define PACKET_LENGTH 6 //[duty, stepwidth(1), stepwidth(2), stepcount(1), stepcount(2), motorState]

#define CLK_SPEED 20000000
//#define PWM_DUTY_PERIOD 400
#define PWM_DUTY_PERIOD (CLK_SPEED / PWM_FREQ)


void ClockSetup(void);
void MotorPreAction(void);
void MotorPostAction(void);
void ProcessPacket(volatile char *data, unsigned char ArrayLength);
void BNCSetup(void);
void L293DSetup(unsigned char duty);
void StepperSetup(unsigned int stepPeriod);
void StepperStart(unsigned int stepCount);
void pulseBNC(void);
void BNCHigh(void);
void BNCLow(void);
void getMotorStatus(void);

static volatile unsigned int stepCounter = 0;
static volatile unsigned int stepCounter_reload = 0;
static volatile unsigned char stepState = 0;
static volatile char motorState = 0; // [7-6:CurrentDirection, 5-0: repeatCount]
static volatile char comState = 0;  // [7:x, 6:x, 5:MotorHeader, 4:HeaderRx, 3-0: PayloadLoc]
static volatile char dataPayload[PACKET_LENGTH];
static volatile unsigned int pulseCounter = 0;

int main(void)
{
	WDTCTL = WDTPW | WDTHOLD;	// stop watchdog timer
	ClockSetup();   // set for 20MHz
	UARTSetup();
	BNCSetup();
//	L293DSetup(100);
//	StepperSetup(613);
//	StepperStart(256);
    __bis_SR_register(GIE);  //enable ISR

    while(1)
    {
        while(pulseCounter)
        {
            BNCHigh();
            unsigned int delayLooper;
            for(delayLooper = DELAY_LOOP_COUNT; delayLooper > 0; delayLooper--);
            pulseCounter = pulseCounter - 1;
        }
        BNCLow();
    }

}

void ClockSetup()
{
    // code for DCO
    CSCTL0 = CSKEY; // unlock clock

    CSCTL1 = DCORSEL + DCOFSEL_1;   // Set for 20MHz
    CSCTL2 = SELA_3 + SELS_3 + SELM_3;   // Set SMCLK, MCLK = DCO
    CSCTL3 = DIVA_5; //ACLK/32
}

void MotorPreAction()
{
    pulseBNC();
}

void MotorPostAction()
{
    pulseBNC();
}


void UARTReceiveAction(unsigned char byte)
{
//    UARTSendByteBlocking(byte);
//    UARTSendByteBlocking(comState);

    _no_operation();

    if(!(comState & BIT4))      // check if header set
    {                               // if no header
        if(byte != PACKET_HEADER)       // if byte is not header
        {
            UARTSendByte(0xFF);             // send error
            comState = 0;                   // reset SM (no effect on current motor)
            return;
        }
        else                            // if byte is header
        {
            comState |= BIT4;               // Set SM
            return;
        }
    }

    else                        // if header
    {
        if(!(comState & BIT5))  // if no motor header
        {
            if(byte == PULSE_CMD)   // if pulse
            {
                pulseBNC();
                comState = 0;                   // reset SM (no effect on current motor)
                return;
            }

            else if(byte == STATUS_REQ)
            {
                getMotorStatus();
                comState = 0;                   // reset SM (no effect on current motor)
                return;
            }

            else if(byte == MOTOR_HEADER)   // if motor cmd
            {
                comState |= BIT5;   //setSM
                return;
            }
            else                            //unknown cmd
            {
                UARTSendByte(0xFF);             // send error
                comState = 0;                   // reset SM (no effect on current motor)
                return;
            }
        }
        else                     //if Motor header
        {
            dataPayload[(comState & 0x0F)] = byte;  // write data to buffer
            comState = (comState & 0xF0) + ((comState + 1) & 0x0F);       // increment pointer

            if((comState & 0x0F) >= PACKET_LENGTH)    // if buffer full
            {
//                UARTSendArray(dataPayload, PACKET_LENGTH);  // echo full cmd
                ProcessPacket(dataPayload, PACKET_LENGTH);  // process cmd
                comState = 0;                   // reset SM (no effect on current motor)
            }
            return;
        }
    }
}

/**
 * takes a payload and starts motor
 */
void ProcessPacket(volatile char *data, unsigned char ArrayLength)
{
    char duty = *data;  // first byte is duty (motor pwm for power)

    int stepPeriod;     // next 2 bytes is period (rotation speed)
    int temp;
    data = data + 1;
    temp = (*data);
    stepPeriod = temp << 8;
    data = data + 1;
    temp = (*data);
    stepPeriod |= (temp) & 0x00FF;

    stepCounter_reload = 0;  // next 2 bytes is step count (num rotations)
    data = data + 1;
    temp = (*data);
    stepCounter_reload = temp << 8;
    data = data + 1;
    temp = (*data);
    stepCounter_reload |= (temp) & 0x00FF;

    data = data + 1; // next byte is motorState
    motorState = *data;

    // excecute commands
    if(stepCounter_reload != 0)
    {
        L293DSetup(duty);
        StepperSetup(stepPeriod);
        StepperStart(stepCounter_reload);
    }
    else
    {
        stepCounter = 0;
        TB0CTL &= ~(MC_3);
        P1SEL0 &= ~(BIT0 + BIT1 + BIT2 + BIT3);
        P1OUT &= ~(BIT0 + BIT1 + BIT2 + BIT3);
    }
}

void BNCSetup(void)
{
    P1DIR |= BIT4 + BIT5;
    P1OUT &= ~(BIT4 + BIT5);
}

void L293DSetup(unsigned char duty)
{
    P1DIR |= BIT0 + BIT1 + BIT2 + BIT3;
    P1OUT &= ~(BIT0 + BIT1 + BIT2 + BIT3);

    int pulseTime = 0;
    if(duty >= 100)
        pulseTime = PWM_DUTY_PERIOD;
    else if(duty == 0)
        pulseTime = 0;
    else
        pulseTime = PWM_DUTY_PERIOD * duty / 100;

//    pulseTime = PWM_DUTY_PERIOD;

    TA0CCR0 = PWM_DUTY_PERIOD;
    TA1CCR0 = PWM_DUTY_PERIOD;

    TA0CCR1 = pulseTime;
    TA0CCR2 = pulseTime;
    TA1CCR1 = pulseTime;
    TA1CCR2 = pulseTime;

    TA0CTL = TASSEL_2 + MC_1 + TACLR; // SMCLK, UPMODE, CLEAR
    TA1CTL = TASSEL_2 + MC_1 + TACLR; // SMCLK, UPMODE, CLEAR

    TA0CCTL1 = OUTMOD_7; // TOGGLE/SET
    TA0CCTL2 = OUTMOD_7; // TOGGLE/SET
    TA1CCTL1 = OUTMOD_7; // TOGGLE/SET
    TA1CCTL2 = OUTMOD_7; // TOGGLE/SET
}

void StepperSetup(unsigned int stepPeriod)
{
    TB0CCR0 = stepPeriod;
    TB0EX0 = TBIDEX_4;  // CLK/5 (FREQUENCY SHOULD BE 62.5kHz)
    TB0CTL = TBSSEL_1 + ID_1 + TBCLR; // ACLK, CLEAR
    TB0CCTL0 = CCIE;
}

void StepperStart(unsigned int stepCount)
{
    stepCounter = stepCount;
    MotorPreAction();
    TB0CTL |= MC_1;  // UPMODE
}

void pulseBNC(void)
{
    pulseCounter = 32768;
}

void BNCHigh(void)
{
    P1OUT |= (BIT4 + BIT5);
}

void BNCLow(void)
{
    P1OUT &= ~(BIT4 + BIT5);
}

void getMotorStatus(void)
{
    unsigned int currStep = stepCounter;
    unsigned int currPulse = pulseCounter;
    unsigned char mstate = motorState;
    unsigned int reloadValue = stepCounter_reload;

    UARTSendByte((currStep >> 8) & 0x00FF);
    UARTSendByte(currStep & 0x00FF);
    UARTSendByte(mstate);
    UARTSendByte((currPulse >> 8) & 0x00FF);
    UARTSendByte(currPulse & 0x00FF);
    UARTSendByte((reloadValue >> 8) & 0x00FF);
    UARTSendByte(reloadValue & 0x00FF);

    return;
}

#pragma vector = TIMER0_B0_VECTOR   //Timer2 B0 interrupt
__interrupt void TIMER0_B0(void)
{
    P1SEL0 &= ~(BIT0 + BIT1 + BIT2 + BIT3);
    P1OUT &= ~(BIT0 + BIT1 + BIT2 + BIT3);

    P1SEL0 |= (0x01 << stepState);  // updates the motor step state

    //advance the motor state
    if(motorState & BIT7)
    {
        stepState = stepState + 1;
        if(stepState > 3)
            stepState =  0;   
    }
    else
    {
        stepState = stepState - 1;
        if(stepState > 3)
            stepState =  3;
    }

    stepCounter = stepCounter - 1;
    if(stepCounter == 0)
    {
        if(motorState & 0x3F)
        {
            motorState = (motorState + 0x40);
//            motorState ^= BIT7;
            motorState = motorState - 1;
            // StepperStart(stepCounter_reload);
            stepCounter = stepCounter_reload;
        }
        else
        {
            TB0CTL &= ~(MC_3);
            P1SEL0 &= ~(BIT0 + BIT1 + BIT2 + BIT3);
            P1OUT &= ~(BIT0 + BIT1 + BIT2 + BIT3);
            MotorPostAction();
        }
    }
}
