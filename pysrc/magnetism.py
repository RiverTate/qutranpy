from scipy.sparse import coo_matrix,bmat
from rotate_spin import sx,sy,sz
from increase_hilbert import get_spinless2full,get_spinful2full
import numpy as np
import checkclass


def add_zeeman(h,zeeman=[0.0,0.0,0.0]):
  """ Add Zeeman to the hamiltonian """
  # convert the input into a list
  def convert(z):
    if checkclass.is_iterable(z): return z # iterable, input is an array
    else: return [0.,0.,z] # input is a number
  from scipy.sparse import coo_matrix as coo
  from scipy.sparse import bmat
  if h.has_spin: # only if the system has spin
   # no = h.num_orbitals # number of orbitals (without spin)
    no = len(h.geometry.r) # number of orbitals (without spin)
    # create matrix to add to the hamiltonian
    bzee = [[None for i in range(no)] for j in range(no)]
    # assign diagonal terms
    if not callable(zeeman): # if it is a number
      for i in range(no):
        zeeman = convert(zeeman) # convert to list
        bzee[i][i] = zeeman[0]*sx+zeeman[1]*sy+zeeman[2]*sz
    elif callable(zeeman): # if it is a function
      r = h.geometry.r  # z position
      for i in range(no):
        mm = zeeman(r[i])  # get the value of the zeeman
        mm = convert(mm) # convert to list
        bzee[i][i] = mm[0]*sx+mm[1]*sy+mm[2]*sz
    else:
      raise
    bzee = bmat(bzee) # create matrix
    h.intra = h.intra + h.spinful2full(bzee) # Add matrix 
  if not h.has_spin:  # still have to implement this...
    raise





def add_antiferromagnetism(h,m,axis):
  """ Adds to the intracell matrix an antiferromagnetic imbalance """
  intra = h.intra # intracell hopping
  if h.geometry.has_sublattice: pass  # if has sublattice
  else: # if does not have sublattice
    print("WARNING, no sublattice present")
    return 0. # if does not have sublattice
  if h.has_spin:
    natoms = len(h.geometry.x) # number of atoms
    out = [[None for j in range(natoms)] for i in range(natoms)] # output matrix
    # create the array
    if checkclass.is_iterable(m): # iterable, input is an array
      mass = m # use the input array
    elif callable(m): # input is a function
      mass = [m(h.geometry.r[i]) for i in range(natoms)] # call the function
    else: # assume it is a float
      mass = [m for i in range(natoms)] # create list
    for i in range(natoms): # loop over atoms
      mi = mass[i] # select the element
      if callable(axis): ax = np.array(axis(h.geometry.r[i])) # call the function
      else: ax = np.array(axis) # convert to array
      ax = ax/np.sqrt(ax.dot(ax)) # normalize the direction
      # add contribution to the Hamiltonian
      out[i][i] = mi*(sx*ax[0] + sy*ax[1] + sz*ax[2])*h.geometry.sublattice[i]
    out = bmat(out) # turn into a matrix
    h.intra = h.intra + h.spinful2full(out) # Add matrix 
  else:
    print("no AF for unpolarized hamiltonian")
    raise






def add_magnetism(h,m):
  """ Adds magnetism to the intracell hopping"""
  intra = h.intra # intracell hopping
  if h.has_spin:
    natoms = len(h.geometry.r) # number of atoms
    # create the array
    out = [[None for j in range(natoms)] for i in range(natoms)] # output matrix
    if checkclass.is_iterable(m):
      print(natoms)
      if checkclass.is_iterable(m[0]) and len(m)==natoms: # input is an array
        mass = m # use as arrays
      elif len(m)==3: # single exchange provided
        mass = [m for i in range(natoms)] # use as arrays
      else: raise
    elif callable(m): # input is a function
      mass = [m(h.geometry.r[i]) for i in range(natoms)] # call the function
    else: 
      print("Wrong input in add_magnetism")
      raise 
    for i in range(natoms): # loop over atoms
      mi = mass[i] # select the element
      # add contribution to the Hamiltonian
      out[i][i] = sx*mi[0] + sy*mi[1] + sz*mi[2]
    out = bmat(out) # turn into a matrix
    h.intra = h.intra + h.spinful2full(out) # Add matrix 
  else:
    print("no AF for unpolarized hamiltonian")
    raise





def add_frustrated_antiferromagnetism(h,m):
  """Add frustrated magnetism"""
  import geometry
  if h.geometry.sublattice_number==3:
    g = geometry.kagome_lattice()
  elif h.geometry.sublattice_number==4:
    g = geometry.pyrochlore_lattice()
    g.center()
  else: raise # not implemented
  ms = []
  for i in range(len(h.geometry.r)): # loop
    ii = h.geometry.sublattice[i] # index of the sublattice
    if callable(m):
      ms.append(-g.r[int(ii)]*m(h.geometry.r[i])) # save this one
    else:
      ms.append(-g.r[int(ii)]*m) # save this one
  h.add_magnetism(ms) # add the magnetization







