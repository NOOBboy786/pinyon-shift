"""Export a qualified layered draw with qrenderdoc --python.

Set PINYON_SHIFT_RENDERDOC_CAPTURE and PINYON_SHIFT_RENDERDOC_EXPORT_DIR.
PINYON_SHIFT_RENDERDOC_EVENT optionally selects the draw (default 21769).
The output directory must not exist. Inputs are for the standalone
pinyon_shift_fh1_owned_geometry_tests executable; no game/save files are changed.
"""
import renderdoc as rd
import pathlib,json,struct,sys,hashlib,os
cap=rd.OpenCaptureFile(); controller=None; report={}; out=None; created=False
def flat(actions):
    for a in actions:
        yield a
        yield from flat(a.children)
try:
    capture=pathlib.Path(os.environ['PINYON_SHIFT_RENDERDOC_CAPTURE'])
    out=pathlib.Path(os.environ['PINYON_SHIFT_RENDERDOC_EXPORT_DIR'])
    out.mkdir(parents=True,exist_ok=False); created=True
    report['capture']=str(capture.resolve())
    status=cap.OpenFile(str(capture),'',None)
    if status!=rd.ResultCode.Succeeded: raise RuntimeError(str(status))
    status,controller=cap.OpenCapture(rd.ReplayOptions(),None)
    if status!=rd.ResultCode.Succeeded: raise RuntimeError(str(status))
    event=int(os.environ.get('PINYON_SHIFT_RENDERDOC_EVENT', '21769'))
    action=next(a for a in flat(controller.GetRootActions()) if a.eventId==event)
    controller.SetFrameEvent(event,True)
    p=controller.GetPipelineState(); reflection=p.GetShaderReflection(rd.ShaderStage.Vertex)
    names={str(r.resourceId):r.name for r in controller.GetResources()}
    if names[str(p.GetGraphicsPipelineObject())]!='VS 3BC346726C1C2535, PS 9584B309533EF6C9':
        raise RuntimeError('Unexpected shader pair at fixture event')
    if action.flags & rd.ActionFlags.Indexed or action.numIndices!=120 or action.numInstances!=1 or action.vertexOffset:
        raise RuntimeError('Unexpected draw parameters at fixture event')
    report['action']={k:str(getattr(action,k)) for k in ('eventId','flags','numIndices','numInstances','vertexOffset','indexOffset','baseVertex')}
    report['constants']=[]; blocks={}
    for i,block in enumerate(reflection.constantBlocks):
        d=p.GetConstantBlock(rd.ShaderStage.Vertex,i,0).descriptor
        size={0:480,1:400,3:768}[block.fixedBindNumber]
        data=bytes(controller.GetBufferData(d.resource,d.byteOffset,size))
        if len(data)!=size: raise RuntimeError('Truncated constant buffer')
        blocks[block.fixedBindNumber]=data
        filename=f'b{block.fixedBindNumber}.bin'; (out/filename).write_bytes(data)
        report['constants'].append(dict(name=block.name,register=block.fixedBindNumber,bytes=len(data),file=filename))
    fetch=struct.unpack('<192I',blocks[3][:768]); system=struct.unpack('<'+str(len(blocks[0])//4)+'I',blocks[0])
    address=fetch[190]&~3; size=(fetch[191]>>2)&0xFFFFFF; size*=4
    report['fetch']=dict(address=address,bytes=size,words=fetch[190:192],system_flags=system[0])
    resources=p.GetReadOnlyResources(rd.ShaderStage.Vertex)
    report['resources']=[dict(resource=str(r.descriptor.resource),offset=r.descriptor.byteOffset,size=r.descriptor.byteSize) for r in resources]
    if len(resources)!=1 or size!=1200 or address+size>resources[0].descriptor.byteSize or system[0]&1:
        raise RuntimeError('Unexpected geometry binding')
    vertices=bytes(controller.GetBufferData(resources[0].descriptor.resource,resources[0].descriptor.byteOffset+address,size))
    if len(vertices)!=size: raise RuntimeError('Truncated geometry')
    (out/'vertices.bin').write_bytes(vertices)
    report['vertices_sha256']=hashlib.sha256(vertices).hexdigest()
    mesh=controller.GetPostVSData(0,0,rd.MeshDataStage.VSOut)
    report['postvs']=dict(stride=mesh.vertexByteStride,vertices=mesh.numIndices)
    (out/'postvs.bin').write_bytes(bytes(controller.GetBufferData(mesh.vertexResourceId,mesh.vertexByteOffset,0)))
except Exception as error: report['error']=str(error)
finally:
    if controller: controller.Shutdown()
    cap.Shutdown()
    if created: (out/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    sys.exit(1 if 'error' in report else 0)
