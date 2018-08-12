import numpy as np

#normalise it
#scalar mult it with a distance 
#subtract it from your position and you have your new position


loc = (71.38400438371752, 105.79405250864147)
enemy_loc = (61.38400438371752, 95.79405250864147)

def normalise(location, enemy_location):
    x1 = np.array(location)
    x2 = np.array(enemy_location)
    x_sub = np.subtract(x1,x2)
    x_added = np.add(x_sub, x1)
    return x_added



def numpy_calculations(location, enemy_location):
    np_retreat = np.array(location)
    np_enemy_loc = np.array(enemy_location)
    #Normalise values
    np_normalise_retreat = np.linalg.norm(np_retreat)
    np_normalise_enemy_retreat = np.linalg.norm(np_enemy_loc)
    #Scalar Multplication
    scalar_values = np.multiply(np_normalise_retreat, np_normalise_enemy_retreat)
    subtract_from_original = np.subtract(np_retreat, scalar_values)
    return subtract_from_original

x = normalise(loc, enemy_loc)
print(tuple(x))





