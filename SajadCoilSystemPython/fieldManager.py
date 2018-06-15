import numpy as np

def field2signal(vectorField):
    ''' 
    A function that reads the inverse of characterization matrix of Sajad's coils from
    a file and outputs the necessary coil currents for a desired magnetic field.
    
    The characterization matrix L is defined in the paper by Salmanipour and Diller 
    "Eight-Degrees-of-Freedom Remote Actuation of Small Magnetic Mechanisms" ICRA 2018
    as U = L*I where I is a vector of input coil currents and U is a vector containing 
    the independent output magnetic field magnitude and gradient components.
    '''
    np.set_printoptions(suppress=True)
    # Load text values containing the matrix elements of L^-1 and reshape to 8x8
    fileName = 'InvActMatElements_new.txt'
    rawData = np.loadtxt(fileName)
    invMatrix = np.reshape(rawData,(8,8))
    # I = (L^-1)*U
    signal = np.dot(invMatrix.transpose(),vectorField)/1000
    return signal

class FieldManager(object):
    def __init__(self,dac):
        self.vecField = [0,0,0,0,0,0,0,0]
        self.dac = dac

    # Uniform field
    def setField(self,vecField):
        signal = field2signal(vecField)
        self.vecField = vecField
        # Amplifier indices corresponding to the coil numbers defined by Sajad
        indexAmplifiers = np.matrix('2; 5; 4; 1; 3; 0; 6; 7')
        for i in range(8):
            self.dac.s826_aoPin(indexAmplifiers.item(i), signal[i])

    def clearField(self):
        self.setField([0,0,0,0,0,0,0,0])
