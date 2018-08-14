from __future__ import print_function
import scipy.sparse.linalg as slg
import scipy.linalg as lg
from scipy.sparse import csc_matrix as csc
from scipy.sparse import csc_matrix 
from scipy.sparse import bmat
import os
import numpy as np
import klist

def ldos0d(h,e=0.0,delta=0.01):
  """Calculates the local density of states of a hamiltonian and
     writes it in file"""
  if h.dimensionality==0:  # only for 0d
    iden = np.identity(h.intra.shape[0],dtype=np.complex) # create identity
    g = ( (e+1j*delta)*iden -h.intra ).I # calculate green function
  else: raise # not implemented...
  d = [ -(g[i,i]).imag/np.pi for i in range(len(g))] # get imaginary part
  d = spatial_dos(h,d) # convert to spatial resolved DOS
  g = h.geometry  # store geometry
  write_ldos(g.x,g.y,d,z=g.z) # write in file
  return d





def ldos0d_wf(h,e=0.0,delta=0.01,num_wf = 10,robust=False,tol=0):
  """Calculates the local density of states of a hamiltonian and
     writes it in file, using arpack"""
  if h.dimensionality==0:  # only for 0d
    intra = csc_matrix(h.intra) # matrix
  else: raise # not implemented...
  if robust: # go to the imaginary axis for stability
    eig,eigvec = slg.eigs(intra,k=int(num_wf),which="LM",
                        sigma=e+1j*delta,tol=tol) 
    eig = eig.real # real part only
  else: # Hermitic Hamiltonian
    eig,eigvec = slg.eigsh(intra,k=int(num_wf),which="LM",sigma=e,tol=tol) 
  d = np.array([0.0 for i in range(intra.shape[0])]) # initialize
  for (v,ie) in zip(eigvec.transpose(),eig): # loop over wavefunctions
    v2 = (np.conjugate(v)*v).real # square of wavefunction
    fac = delta/((e-ie)**2 + delta**2) # factor to create a delta
    d += fac*v2 # add contribution
#  d /= num_wf # normalize
  d /= np.pi # normalize
  d = spatial_dos(h,d) # resum if necessary
  g = h.geometry  # store geometry
  write_ldos(g.x,g.y,d,z=g.z) # write in file




def ldos_arpack(intra,num_wf=10,robust=False,tol=0,e=0.0,delta=0.01):
  """Use arpack to calculate hte local density of states at a certain energy"""
  if robust: # go to the imaginary axis for stability
    eig,eigvec = slg.eigs(intra,k=int(num_wf),which="LM",
                        sigma=e+1j*delta,tol=tol) 
    eig = eig.real # real part only
  else: # Hermitic Hamiltonian
    eig,eigvec = slg.eigsh(intra,k=int(num_wf),which="LM",sigma=e,tol=tol) 
  d = np.array([0.0 for i in range(intra.shape[0])]) # initialize
  for (v,ie) in zip(eigvec.transpose(),eig): # loop over wavefunctions
    v2 = (np.conjugate(v)*v).real # square of wavefunction
    fac = delta/((e-ie)**2 + delta**2) # factor to create a delta
    d += fac*v2 # add contribution
#  d /= num_wf # normalize
  d /= np.pi # normalize
  return d



def ldos_waves(intra,es = [0.0],delta=0.01):
  """Calculate the DOS in a set of energies by full diagonalization"""
  es = np.array(es) # array with energies
  eig,eigvec = lg.eigh(intra) 
  ds = [] # empty list
  for energy in es: # loop over energies
    d = np.array([0.0 for i in range(intra.shape[0])]) # initialize
    for (v,ie) in zip(eigvec.transpose(),eig): # loop over wavefunctions
      v2 = (np.conjugate(v)*v).real # square of wavefunction
      fac = delta/((energy-ie)**2 + delta**2) # factor to create a delta
      d += fac*v2 # add contribution
    d /= np.pi # normalize
    ds.append(d) # store
  ds = np.array(ds) # convert to array
  return ds



def ldosmap(h,energies=np.linspace(-1.0,1.0,40),delta=None,nk=40):
  """Write a map of the ldos using full diagonalization"""
  if delta is None:
    delta = (np.max(energies)-np.min(energies))/len(energies) # delta
  hkgen = h.get_hk_gen() # get generator
  dstot = np.zeros((len(energies),h.intra.shape[0])) # initialize
  for ik in range(nk): 
    print("Random k-point",ik,nk,end="\r")
    k = np.random.random(3) # random k-point
    hk = hkgen(k) # ge Hamiltonian
    ds = ldos_waves(hk,es=energies,delta=delta) # LDOS for this kpoint
    dstot += ds # add
  print("LDOS finished")
  dstot /=nk # normalize
  dstot = [spatial_dos(h,d) for d in dstot] # convert to spatial resolved DOS
  return np.array(dstot)



def slabldos(h,energies=np.linspace(-1.0,1.0,40),delta=None,nk=40):
  """Computes the DOS for each site of an slab, only for 2d"""
  if h.dimensionality!=2: raise # nope
  ds = ldosmap(h,energies=energies,delta=delta,nk=nk)
  if len(ds[0])!=len(h.geometry.z): 
    print("Wrong dimensions",len(ds[0]),len(h.geometry.z))
    raise
  f = open("DOSMAP.OUT","w")
  f.write("# energy, index, DOS, zposition\n")
  for ie in range(len(energies)):
    for iz in range(len(h.geometry.z)):
      f.write(str(energies[ie])+"  ")
      f.write(str(iz)+"  ")
      f.write(str(ds[ie,iz])+"   ")
      f.write(str(h.geometry.z[iz])+"\n")
  f.close()
  return energies,np.transpose(ds) # retunr LDOS 










def ldos1d(h,e=0.0,delta=0.001,nrep=3):
  """ Calculate DOS for a 1d system"""
  import green
  if h.dimensionality!=1: raise # only for 1d
  gb,gs = green.green_renormalization(h.intra,h.inter,energy=e,delta=delta)
  d = [ -(gb[i,i]).imag for i in range(len(gb))] # get imaginary part
  d = spatial_dos(h,d) # convert to spatial resolved DOS
  g = h.geometry  # store geometry
  x,y = g.x,g.y # get the coordinates
  go = h.geometry.copy() # copy geometry
  go = go.supercell(nrep) # create supercell
  write_ldos(go.x,go.y,d.tolist()*nrep) # write in file
  return d




def ldos2d(h,e=0.0,delta=0.001,nrep=3,nk=None,mode="green",
             random=True,num_wf=20):
  """ Calculate DOS for a 2d system"""
  if mode=="green":
    import green
    if h.dimensionality!=2: raise # only for 1d
    if nk is not None:
      print("LDOS using normal integration with nkpoints",nk)
      gb,gs = green.bloch_selfenergy(h,energy=e,delta=delta,mode="full",nk=nk)
      d = [ -(gb[i,i]).imag for i in range(len(gb))] # get imaginary part
    else:
      print("LDOS using renormalization adaptative Green function")
      gb,gs = green.bloch_selfenergy(h,energy=e,delta=delta,mode="adaptive")
      d = [ -(gb[i,i]).imag for i in range(len(gb))] # get imaginary part
  elif mode=="arpack": # arpack diagonalization
    import klist
    if nk is None: nk = 10
    hkgen = h.get_hk_gen() # get generator
    ds = [] # empty list
    for k in klist.kmesh(h.dimensionality,nk=nk): # loop over kpoints
      print("Doing",k)
      if random:
        print("Random k-point")
        k = np.random.random(3) # random k-point
      hk = csc_matrix(hkgen(k)) # get Hamiltonian
      ds += [ldos_arpack(hk,num_wf=num_wf,robust=False,
                     tol=0,e=e,delta=delta)]
    d = ds[0]*0.0 # inititlize
    for di in ds: d += di # add
    d /=len(ds) # normalize
  d = spatial_dos(h,d) # convert to spatial resolved DOS
  g = h.geometry  # store geometry
  x,y = g.x,g.y # get the coordinates
  go = h.geometry.copy() # copy geometry
  go = go.supercell(nrep) # create supercell
  write_ldos(go.x,go.y,d.tolist()*(nrep**2),z=go.z) # write in file


ldos = ldos2d


def multi_ldos(h,es=[0.0],delta=0.001,nrep=3,nk=2,numw=3,random=False):
  """Calculate many LDOS, by diagonalizing the Hamiltonian"""
  print("Calculating eigenvectors in LDOS")
  if h.is_sparse: # sparse Hamiltonian
    from bandstructure import smalleig
    print("SPARSE Matrix")
    evals,ws = [],[] # empty list
    ks = klist.kmesh(h.dimensionality,nk=nk) # get grid
    hk = h.get_hk_gen() # get generator
    for k in ks: # loop
      print("Diagonalizing in LDOS, SPARSE mode")
      if random:
        k = np.random.random(3) # random vector
        print("RANDOM vector in LDOS")
      e,w = smalleig(hk(k),numw=numw,evecs=True)
      evals += [ie for ie in e]
      ws += [iw for iw in w]
#      evals = np.concatenate([evals,e]) # store
#      ws = np.concatenate([ws,w]) # store
#    raise
#    (evals,ws) = h.eigenvectors(nk) # get the different eigenvectors
  else:
    print("DENSE Matrix")
    (evals,ws) = h.eigenvectors(nk) # get the different eigenvectors
  ds = [(np.conjugate(v)*v).real for v in ws] # calculate densities
  del ws # remove the wavefunctions
  os.system("rm -rf MULTILDOS") # remove folder
  os.system("mkdir MULTILDOS") # create folder
  go = h.geometry.copy() # copy geometry
  go = go.supercell(nrep) # create supercell
  fo = open("MULTILDOS/MULTILDOS.TXT","w") # files with the names
  for e in es: # loop over energies
    print("MULTILDOS for energy",e)
    out = np.array([0.0 for i in range(h.intra.shape[0])]) # initialize
    for (d,ie) in zip(ds,evals): # loop over wavefunctions
      fac = delta/((e-ie)**2 + delta**2) # factor to create a delta
      out += fac*d # add contribution
    out /= np.pi # normalize
    out = spatial_dos(h,out) # resum if necessary
    name0 = "LDOS_"+str(e)+"_.OUT" # name of the output
    name = "MULTILDOS/" + name0
    write_ldos(go.x,go.y,out.tolist()*(nrep**h.dimensionality),
                  output_file=name) # write in file
    fo.write(name0+"\n") # name of the file
    fo.flush() # flush
  fo.close() # close file
  # Now calculate the DOS
  from dos import calculate_dos
  es2 = np.linspace(min(es),max(es),len(es)*10)
  ys = calculate_dos(evals,es2,delta) # use the Fortran routine
  from dos import write_dos
  write_dos(es2,ys,output_file="MULTILDOS/DOS.OUT")  













def spatial_dos(h,dos):
  """Resums a certain DOS to show only the spatial dependence"""
  if h.has_spin == False and h.has_eh==False: return np.array(dos)
  elif h.has_spin == True and h.has_eh==False: 
    return np.array([dos[2*i]+dos[2*i+1] for i in range(len(dos)//2)])
  elif h.has_spin == False and h.has_eh==True: 
    return np.array([dos[2*i]+dos[2*i+1] for i in range(len(dos)//2)])
  elif h.has_spin == True and h.has_eh==True: 
    return np.array([dos[4*i]+dos[4*i+1]+dos[4*i+2]+dos[4*i+3] for i in range(len(dos)//4)])
  else: raise


def write_ldos(x,y,dos,output_file="LDOS.OUT",z=None):
  """ Write LDOS in a file"""
  fd = open(output_file,"w")   # open file
  fd.write("# x,  y, local density of states\n")
  ii = 0
  for (ix,iy,idos) in zip(x,y,dos): # write everything
    fd.write(str(ix) +"   "+ str(iy) + "   "+ str(idos))
    if z is not None: fd.write("   "+str(z[ii]))
    fd.write("\n")
    ii += 1
  fd.close() # close file




def ldos_finite(h,e=0.0,n=10,nwf=4,delta=0.0001):
  """Calculate the density of states for a finite system"""
  if h.dimensionality!=1: raise # if it is not one dimensional
  intra = csc(h.intra) # convert to sparse
  inter = csc(h.inter) # convert to sparse
  interH = inter.H # hermitian
  m = [[None for i in range(n)] for j in range(n)] # full matrix
  for i in range(n): # add intracell
    m[i][i] = intra
  for i in range(n-1): # add intercell
    m[i][i+1] = inter
    m[i+1][i] = interH
  m = bmat(m) # convert to matrix
  (ene,wfs) = slg.eigsh(m,k=nwf,which="LM",sigma=0.0) # diagonalize
  wfs = wfs.transpose() # transpose wavefunctions
  dos = (wfs[0].real)*0.0 # calculate dos
  for (ie,f) in zip(ene,wfs): # loop over waves
    c = 1./(1.+((ie-e)/delta)**2) # calculate coefficient
    dos += np.abs(f)*c # add contribution
  odos = spatial_dos(h,dos) # get the spatial distribution
  go = h.geometry.supercell(n) # get the supercell
  write_ldos(go.x,go.y,odos) # write in a file
  return dos # return the dos





def ldos_defect(h,v,e=0.0,delta=0.001,n=1):
  """Calculates the LDOS of a cell with a defect, writting the n
  neighring cells"""
  raise # still not finished
  import green
  # number of repetitions
  rep = 2*n +1
  # calculate pristine green function
  g,selfe = green.supercell_selfenergy(h,e=e,delta=delta,nk=100,nsuper=rep)
  # now calculate defected green function 
  ez = e + 1j*delta # complex energy
  emat = np.matrix(np.identity(len(g)))*ez  # E +i\delta 
  import supercell
  pintra = supercell.intra_super2d(h,n=rep) # pristine
  vintra = supercell.intra_super2d(h,n=rep,central=v) # defective
  selfe = emat - pintra - g.I # dyson euqation, get selfenergy
  gv = (emat - vintra -selfe).I   # Green function of a vacancy, with selfener
  return



