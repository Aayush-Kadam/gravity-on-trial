"""Halo squared circular speeds in kpc, km/s and solar masses."""
import numpy as np
G=4.30091e-6
H0=.073
def check(r,p):
    r=np.asarray(r,dtype=float)
    if np.any(~np.isfinite(r)) or np.any(r<=0) or not np.all(np.isfinite(p)):
        raise ValueError('Finite strictly positive radii and finite log parameters required')
    return r
def nfw(r,p):
    r=check(r,p); mass,c=10.**np.asarray(p)
    R200=(G*mass/(100*H0**2))**(1/3)
    x=c*r/R200
    f=np.log1p(x)-x/(1+x)
    small=x<.001
    f[small]=sum(((-1.)**n)*(n-1)/n*x[small]**n for n in range(2,10))
    return G*mass*f/(np.log1p(c)-c/(1+c))/r
def burkert(r,p):
    r=check(r,p); rho,r0=10.**np.asarray(p); x=r/r0
    b=2*np.log1p(x)+np.log1p(x*x)-2*np.arctan(x)
    small=x<.01
    b[small]=4*(x[small]**3/3-x[small]**4/4+x[small]**7/7-x[small]**8/8)
    return G*np.pi*rho*r0**3*b/r
