# library to deal with the spectral properties of the hamiltonian
import numpy as np
import scipy.linalg as lg
import scipy.sparse.linalg as slg
import kpm
import os
from operators import operator2list

arpack_tol = 1e-5
arpack_maxiter = 10000

def fermi_surface(h,write=True,output_file="FERMI_MAP.OUT",
                    e=0.0,nk=50,nsuper=1,reciprocal=True,
                    delta=None,refine_delta=1.0,operator=None,
                    mode='full',num_waves=2,info=True):
  """Calculates the Fermi surface of a 2d system"""
  if operator is None:
    operator = np.matrix(np.identity(h.intra.shape[0]))
  if h.dimensionality!=2: raise  # continue if two dimensional
  hk_gen = h.get_hk_gen() # gets the function to generate h(k)
  kxs = np.linspace(-nsuper,nsuper,nk)  # generate kx
  kys = np.linspace(-nsuper,nsuper,nk)  # generate ky
  iden = np.identity(h.intra.shape[0],dtype=np.complex)
  kdos = [] # empty list
  kxout = []
  kyout = []
  if reciprocal: R = h.geometry.get_k2K() # get matrix
  else:  R = np.matrix(np.identity(3)) # get identity
  # setup a reasonable value for delta
  if delta is None:
 #   delta = 1./refine_delta*2.*np.max(np.abs(h.intra))/nk
    delta = 1./refine_delta*2./nk

  #### function to calculate the weight ###
  if mode=='full': # use full inversion
    def get_weight(hk):
      gf = ((e+1j*delta)*iden - hk).I # get green function
      if callable(operator):
        tdos = -(operator(x,y)*gf).imag # get imaginary part
      else: tdos = -(operator*gf).imag # get imaginary part
      return tdos.trace()[0,0].real # return traze
  elif mode=='lowest': # use full inversion
    def get_weight(hk):
      es,waves = slg.eigsh(hk,k=num_waves,sigma=0.0,tol=arpack_tol,which="LM",
                            maxiter = arpack_maxiter)
      return np.sum(delta/(es*es+delta*delta)) # return weight

##############################################


  # setup the operator
  for x in kxs:
    for y in kxs:
      if info: print("Doing",x,y)
      r = np.matrix([x,y,0.]).T # real space vectors
      k = np.array((R*r).T)[0] # change of basis
      hk = hk_gen(k) # get hamiltonian
      kdos.append(get_weight(hk)) # add to the list
#      kdos.append(np.sum([tdos[i,i]*(-1)**i for i in range(tdos.shape[0])])) # add to the list
      kxout.append(x)
      kyout.append(y)
  if write:  # optionally, write in file
    f = open(output_file,"w") 
    for (x,y,d) in zip(kxout,kyout,kdos):
      f.write(str(x)+ "   "+str(y)+"   "+str(d)+"\n")
    f.close() # close the file
  return (kxout,kyout,d) # return result




def boolean_fermi_surface(h,write=True,output_file="BOOL_FERMI_MAP.OUT",
                    e=0.0,nk=50,nsuper=1,reciprocal=False,
                    delta=None):
  """Calculates the Fermi surface of a 2d system"""
  if h.dimensionality!=2: raise  # continue if two dimensional
  hk_gen = h.get_hk_gen() # gets the function to generate h(k)
  kxs = np.linspace(-nsuper,nsuper,nk)  # generate kx
  kys = np.linspace(-nsuper,nsuper,nk)  # generate ky
  kdos = [] # empty list
  kxout = []
  kyout = []
  if reciprocal: R = h.geometry.get_k2K() # get matrix
  # setup a reasonable value for delta
  if delta is None:
    delta = 8./np.max(np.abs(h.intra))/nk
  for x in kxs:
    for y in kxs:
      r = np.matrix([x,y,0.]).T # real space vectors
      k = np.array((R*r).T)[0] # change of basis
      hk = hk_gen(k) # get hamiltonian
      evals = lg.eigvalsh(hk) # diagonalize
      de = np.abs(evals - e) # difference with respect to fermi
      de = de[de<delta] # energies close to fermi
      if len(de)>0: kdos.append(1.0) # add to the list
      else: kdos.append(0.0) # add to the list
      kxout.append(x)
      kyout.append(y)
  if write:  # optionally, write in file
    f = open(output_file,"w") 
    for (x,y,d) in zip(kxout,kyout,kdos):
      f.write(str(x)+ "   "+str(y)+"   "+str(d)+"\n")
    f.close() # close the file
  return (kxout,kyout,d) # return result






















from bandstructure import braket_wAw


def selected_bands2d(h,output_file="BANDS2D_",nindex=[-1,1],
               nk=50,nsuper=1,reciprocal=True,
               operator=None,k0=[0.,0.]):
  """ Calculate a selected bands in a 2d Hamiltonian"""
  if h.dimensionality!=2: raise  # continue if two dimensional
  hk_gen = h.get_hk_gen() # gets the function to generate h(k)
  kxs = np.linspace(-nsuper,nsuper,nk)+k0[0]  # generate kx
  kys = np.linspace(-nsuper,nsuper,nk)+k0[1]  # generate ky
  kdos = [] # empty list
  kxout = []
  kyout = []
  if reciprocal: R = h.geometry.get_k2K() # get matrix
  else:  R = np.matrix(np.identity(3)) # get identity
  # setup a reasonable value for delta
  # setup the operator
  operator = operator2list(operator) # convert into a list
  os.system("rm -f "+output_file+"*") # delete previous files
  fo = [open(output_file+"_"+str(i)+".OUT","w") for i in nindex] # files        
  for x in kxs:
    for y in kxs:
      print("Doing",x,y)
      r = np.matrix([x,y,0.]).T # real space vectors
      k = np.array((R*r).T)[0] # change of basis
      hk = hk_gen(k) # get hamiltonian
      if not h.is_sparse: evals,waves = lg.eigh(hk) # eigenvalues
      else: evals,waves = slg.eigsh(hk,k=max(nindex)*2,sigma=0.0,
             tol=arpack_tol,which="LM") # eigenvalues
      waves = waves.transpose() # transpose
      epos,wfpos = [],[] # positive
      eneg,wfneg = [],[] # negative
      for (e,w) in zip(evals,waves): # loop
        if e>0.0: # positive
          epos.append(e)
          wfpos.append(w)
        else: # negative
          eneg.append(e)
          wfneg.append(w)
      # now sort the waves
      wfpos = [yy for (xx,yy) in sorted(zip(epos,wfpos))] 
      wfneg = [yy for (xx,yy) in sorted(zip(-np.array(eneg),wfneg))] 
      epos = sorted(epos)
      eneg = -np.array(sorted(-np.array(eneg)))
#      epos = sorted(evals[evals>0]) # positive energies
#      eneg = -np.array(sorted(np.abs(evals[evals<0]))) # negative energies
      for (i,j) in zip(nindex,range(len(nindex))): # loop over desired bands
        fo[j].write(str(x)+"     "+str(y)+"   ")
        if i>0: # positive
          fo[j].write(str(epos[i-1])+"  ")
          for op in operator: # loop over operators
            c = braket_wAw(wfpos[i-1],op).real # expectation value
            fo[j].write(str(c)+"  ") # write in file
          fo[j].write("\n") # write in file
          
        if i<0: # negative
          fo[j].write(str(eneg[abs(i)-1])+"\n")
          for op in operator: # loop over operators
            c = braket_wAw(wfneg[abs(i)-1],op).real # expectation value
            fo[j].write(str(c)+"  ") # write in file
          fo[j].write("\n") # write in file
  [f.close() for f in fo] # close file


get_bands = selected_bands2d




def ev2d(h,nk=50,nsuper=1,reciprocal=False,
               operator=None,k0=[0.,0.],kreverse=False):
  """ Calculate the expectation value of a certain operator"""
  if h.dimensionality!=2: raise  # continue if two dimensional
  hk_gen = h.get_hk_gen() # gets the function to generate h(k)
  kxs = np.linspace(-nsuper,nsuper,nk,endpoint=True)+k0[0]  # generate kx
  kys = np.linspace(-nsuper,nsuper,nk,endpoint=True)+k0[1]  # generate ky
  if kreverse: kxs,kys = -kxs,-kys
  kdos = [] # empty list
  kxout = []
  kyout = []
  if reciprocal: R = h.geometry.get_k2K() # get matrix
  else:  R = np.matrix(np.identity(3)) # get identity
  # setup the operator
  operator = operator2list(operator) # convert into a list
  fo = open("EV2D.OUT","w") # open file
  for x in kxs:
    for y in kxs:
      print("Doing",x,y)
      r = np.matrix([x,y,0.]).T # real space vectors
      k = np.array((R*r).T)[0] # change of basis
      hk = hk_gen(k) # get hamiltonian
      if not h.is_sparse: evals,waves = lg.eigh(hk) # eigenvalues
      else: evals,waves = slg.eigsh(hk,k=max(nindex)*2,sigma=0.0,
             tol=arpack_tol,which="LM") # eigenvalues
      waves = waves.transpose() # transpose
      eneg,wfneg = [],[] # negative
      for (e,w) in zip(evals,waves): # loop
        if e<0: # negative
          eneg.append(e)
          wfneg.append(w)
      fo.write(str(x)+"     "+str(y)+"   ") # write k-point
      for op in operator: # loop over operators
          c = sum([braket_wAw(w,op) for w in wfneg]).real # expectation value
          fo.write(str(c)+"  ") # write in file
      fo.write("\n") # write in file
  fo.close() # close file  





def ev(h,operator=None,nk=30):
  """Calculate the expectation value of a certain number of operators"""
  from densitymatrix import full_dm
  dm = full_dm(h,nk=nk,use_fortran=True)
  if operator is None: # no operator given on input
    operator = [] # empty list
  elif not isinstance(operator,list): # if it is not a list
    operator = [operator] # convert to list
  out = [(dm*op).trace()[0,0] for op in operator] 
  return out # return the result






def total_energy(h,nk=10,nbands=None,use_kpm=False,random=True,kp=None):
  """Return the total energy"""
  if h.is_sparse and not use_kpm: 
    print("Sparse Hamiltonian but no bands given, taking 20")
    nbands=20
  from klist import kmesh
  if kp is None: # no kpoints given
    kp = kmesh(h.dimensionality,nk=nk)
    if random==True: # random k-mesh
      kp = [np.random.random(3) for k in kp]
  f = h.get_hk_gen() # get generator
  etot = 0.0 # initialize
  iv = 0
  for k in kp: # loop over kpoints
    hk = f(k)  # kdependent hamiltonian
    if use_kpm: # Kernel polynomial method
      etot += kpm.total_energy(hk,scale=10.,ntries=20,npol=100) # using KPM
    else: # conventional diagonalization
      if nbands is None: vv = lg.eigvalsh(hk) # diagonalize k hamiltonian
      else: vv,aa = slg.eigsh(hk,k=nbands,which="LM",sigma=0.0) 
      etot += np.sum(vv[vv<0.0]) # sum energies below fermi energy
  etot = etot/len(kp) # normalize
  return etot



