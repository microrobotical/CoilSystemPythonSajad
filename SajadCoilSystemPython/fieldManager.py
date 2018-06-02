import numpy as np

# assign pin # to the coil
# PIN_X1 = [0, 5.003] # pin number, factor number (mT/V)
# PIN_X2 = [3, 4.879]
# PIN_Y1 = [4, 5.143]
# PIN_Y2 = [1, 5.024]
# PIN_Z1 = [2, 5.024]
# PIN_Z2 = [5, 4.433]
GAIN = np.array([4.03, 3.44, 3.92, 3.90, 3.81, 3.95, 4.01, 4.00])


def field2signal(vectorField):
    ''' a function that reads the inverse of characterization matrix of Sajad's coils '''
    np.set_printoptions(suppress=True)
    fileName = 'InvActMatElements_new.txt'
    rawData = np.loadtxt(fileName)
    invMatrix = np.reshape(rawData,(8,8))
    signal = np.dot(invMatrix.transpose(),vectorField)/1000
    return signal



class FieldManager(object):
    def __init__(self,dac):
        self.vecField = [0,0,0,0,0,0,0,0]
        self.dac = dac
        field2signal([5,5,5,0,0,0,0,0])

    # Uniform field
    def setField(self,vecField):
        signal = field2signal(vecField)
        self.vecField = vecField
        indexAmplifiers = np.matrix([[2],[5],[4],[1],[3],[0],[6],[7]])
        for i in range(8):
            self.dac.s826_aoPin(indexAmplifiers.item(i), signal[i])

    def clearField(self):
        self.setField([0,0,0,0,0,0,0,0])
