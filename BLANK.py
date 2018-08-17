import numpy as np


a = (0, 0)
b = (10, 0)
c = (0, 1)



def find_move_vec(unit_loc, *args):
    friendly_unit_loc = np.array(unit_loc)
    enemy_loc = np.array([0,0])
    for loc in args:
        vec = np.array(loc)
        vec = np.add(vec, -friendly_unit_loc)
        #find vector length before normalizing.
        vec_len = np.sqrt(vec[0] ** 2 + vec[1] ** 2)
        norm_vec = np.divide(vec, vec_len)  
        enemy_loc = np.add(enemy_loc, norm_vec) 
    move_vec = friendly_unit_loc - enemy_loc
    return move_vec

#normalize the movement_vector, and then add to the reapers location. Tune pressure vectors?
example = find_move_vec(a, b, c)
print(example)


