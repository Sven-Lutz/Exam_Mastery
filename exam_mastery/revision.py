"""Bounded declarative content correction. Never patch code, policy or source files."""
import copy
from .common import ContractError
ALLOWED={'blueprint','research','author','assessment','cards','interaction','design','learning_plan'}
def apply(bundle,response):
    patches=response.get('patches')
    if not isinstance(patches,list) or not 1<=len(patches)<=80:raise ContractError('Revision requires 1..80 patches')
    result=copy.deepcopy(bundle)
    for patch in patches:
        op=patch.get('op');path=patch.get('path','')
        if op not in ('replace','add','remove') or not isinstance(path,str) or not path.startswith('/'):raise ContractError('Invalid patch operation')
        keys=[k.replace('~1','/').replace('~0','~') for k in path[1:].split('/')]
        if not 2<=len(keys)<=12 or keys[0] not in ALLOWED:raise ContractError('Patch outside learning content')
        current=result
        for key in keys[:-1]:
            if isinstance(current,list):
                index=int(key)
                if not 0<=index<len(current):raise ContractError('Patch traversal index outside bounds')
                current=current[index]
            else:current=current[key]
        key=keys[-1]
        if isinstance(current,list):
            index=len(current) if key=='-' else int(key)
            if index<0 or index>len(current) or (op!='add' and index==len(current)):raise ContractError('Patch list index outside bounds')
            if op=='add':current.insert(index,patch['value'])
            elif op=='remove':current.pop(index)
            else:current[index]=patch['value']
        elif isinstance(current,dict):
            if op in ('remove','replace') and key not in current:raise ContractError('Patch key does not exist')
            if op=='remove':del current[key]
            else:current[key]=patch['value']
        else:raise ContractError('Patch target must be a container')
    if result['blueprint'].get('course_id')!=bundle['blueprint'].get('course_id'):raise ContractError('Revision cannot change course identity')
    return result
