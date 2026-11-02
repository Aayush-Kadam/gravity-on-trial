"""M1 models, units and catalog-frame geometry; Gate 0 halo module unchanged."""
from dataclasses import dataclass
import numpy as np
from .halos import nfw,burkert
KPC_M=3.085677581491367e19
A0=1.2e-10

class DomainError(ValueError):
    def __init__(self,message,indices=()):
        super().__init__(message); self.indices=list(map(int,indices))

def signed_baryons(gas,disk,bulge,ud=.5,ub=.7):
    if not np.all(np.isfinite([ud,ub])) or min(ud,ub)<0:
        raise DomainError('Stellar M/L must be finite and nonnegative (solar units)')
    gas,disk,bulge=np.broadcast_arrays(np.asarray(gas,float),np.asarray(disk,float),np.asarray(bulge,float))
    if not all(np.all(np.isfinite(v)) for v in [gas,disk,bulge]): raise DomainError('Nonfinite component')
    return ud*disk**2+ub*bulge**2+gas*np.abs(gas)

def speed(squared):
    squared=np.asarray(squared,float)
    bad=np.flatnonzero((squared<0)|~np.isfinite(squared))
    if len(bad): raise DomainError('Negative/nonfinite total squared speed; no clamping',bad)
    return np.sqrt(squared)

def rar_acceleration(gbar,a0=A0):
    gbar=np.asarray(gbar,float)
    bad=np.flatnonzero((gbar<=0)|~np.isfinite(gbar))
    if len(bad) or not np.isfinite(a0) or a0<=0: raise DomainError('RAR requires strictly positive baryonic acceleration and a0',bad)
    return gbar/(-np.expm1(-np.sqrt(gbar/a0)))

def rar_speed(r_kpc,bar_sq):
    r=np.asarray(r_kpc,float)
    if np.any(r<=0) or np.any(~np.isfinite(r)): raise DomainError('Positive finite physical radii required')
    return np.sqrt(rar_acceleration(np.asarray(bar_sq)*1e6/(r*KPC_M))*r*KPC_M)/1000

def inclination_factor(catalog_deg,new_deg):
    if not all(np.isfinite([catalog_deg,new_deg])) or not (0<catalog_deg<=90 and 0<new_deg<=90): raise DomainError('Inclinations must lie in (0,90] degrees')
    return np.sin(np.deg2rad(new_deg))/np.sin(np.deg2rad(catalog_deg))

def distance_transform(r,bar_sq,ratio):
    if not np.isfinite(ratio) or ratio<=0: raise DomainError('Distance ratio must be positive')
    return np.asarray(r)*ratio,np.asarray(bar_sq)*ratio

@dataclass
class Curve:
    galaxy: str
    r: np.ndarray
    obs: np.ndarray
    err: np.ndarray
    gas: np.ndarray
    disk: np.ndarray
    bulge: np.ndarray
    metadata: dict
    def validate(self):
        arrays=[np.asarray(getattr(self,name),float) for name in ['r','obs','err','gas','disk','bulge']]
        if not len(arrays[0]) or any(a.ndim!=1 or a.shape!=arrays[0].shape for a in arrays): raise DomainError('Nonempty aligned 1D arrays required')
        if any(np.any(~np.isfinite(a)) for a in arrays): raise DomainError('Missing/nonfinite observations: explicit rejection, no mask changes')
        if np.any(arrays[0]<=0) or np.any(arrays[2]<=0): raise DomainError('Radius/error must be positive')
        if np.any(np.diff(arrays[0])<=0): raise DomainError('Repeated/unordered radii require explicit policy; rejected')
        required=['D','e_D','Inc','e_Inc']
        if any(key not in self.metadata for key in required): raise DomainError('Missing required catalog geometry/uncertainty metadata')
        if not all(np.isfinite(self.metadata[key]) for key in required): raise DomainError('Nonfinite catalog geometry/uncertainty metadata')
        inclination_factor(self.metadata['Inc'],self.metadata['Inc'])
        if self.metadata['D']<=0 or min(self.metadata['e_D'],self.metadata['e_Inc'])<0: raise DomainError('Positive distance and nonnegative geometry errors required')
        for name,array in zip(['r','obs','err','gas','disk','bulge'],arrays):setattr(self,name,array)
        return self

def predict(curve,model,halo=(),ud=.5,ub=.7,d=1.,inc=None):
    bar=signed_baryons(curve.gas,curve.disk,curve.bulge,ud,ub)
    r,bar=distance_transform(curve.r,bar,d)
    if model=='baryons': physical=speed(bar)
    elif model=='rar': physical=rar_speed(r,bar)
    elif model in ['nfw','burkert']:
        if len(halo)!=2 or not np.all(np.isfinite(halo)) or np.any(np.abs(halo)>100): raise DomainError('Two finite bounded log halo parameters required')
        physical=speed(bar+{'nfw':nfw,'burkert':burkert}[model](r,halo))
    else: raise ValueError('Unknown model')
    return physical*inclination_factor(curve.metadata['Inc'],curve.metadata['Inc'] if inc is None else inc)
