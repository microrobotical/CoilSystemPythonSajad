import numpy as np

# Amplifier gains from amplifier signal input in [V] to output in [A].
#   currents = GAIN*signal
GAIN = np.array([4.03, 3.44, 3.92, 3.90, 3.81, 3.95, 4.01, 4.00])


def field2signal(vectorField):
    ''' 
    A function that reads the inverse of the characterization matrix L
    of Sajad's coils from a file and returns the voltage signals to the
    amplifiers given a desired vector field.
    The 8x8 characterization matrix L is defined in the equation
        vectorField = L*signal
    where vectorField is a vector of the 8 independent magnetic field
    values and signal is a vector of the voltage signals sent to each
    of the 8 electromagnetic coil amplifiers. The voltage input signal
    is directly proportional to the amplifier output current.
    '''
    np.set_printoptions(suppress=True)
    # Read the L^-1 values from a file and reshape them into an 8x8 matrix
    fileName = 'InvActMatElements_new.txt'
    rawData = np.loadtxt(fileName)
    invMatrix = np.reshape(rawData,(8,8))
    # Note: Sajad recorded the values as col 1 followed by col 2, etc.
    # Therefore the actual L^inv is the transpose of invMatrix
    # Convert vectorField in mT and mT/m to T and T/m
    signal = np.matmul(invMatrix.transpose(),vectorField/1000)
    return signal



class FieldManager(object):
    def __init__(self,dac):
        self.vecField = [0,0,0,0,0,0,0,0]
        self.dac = dac

    # Uniform field
    def setField(self,vecField):
        signal = field2signal(vecField)
        self.vecField = vecField
        # Map the amplifiers 1-8 to the correct s826 pinouts
        # e.g. Amplifier 2 corresponds to s826 Pin 5
        indexAmplifiers = np.matrix([[2],[5],[4],[1],[3],[0],[6],[7]])
        # Output the signals from each pin
        for i in range(8):
            self.dac.s826_aoPin(indexAmplifiers.item(i), signal[i])

    def clearField(self):
        self.setField([0,0,0,0,0,0,0,0])
