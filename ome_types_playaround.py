from ome_types import to_xml, OME
from ome_types.model import Project, ProjectRef
from ome_types.model import Dataset, DatasetRef
from ome_types.model import Image, ImageRef, Pixels
from ome_types.model import TagAnnotation, MapAnnotation, ROI
from ome_types.model import AnnotationRef, ROIRef, Map
from ome_types.model.map import M
from omero.model import TagAnnotationI, MapAnnotationI
import ezomero
import argparse

def create_proj_and_ref(**kwargs):
    proj = Project(**kwargs)
    proj_ref = ProjectRef(id=proj.id)
    return proj, proj_ref

def create_dataset_and_ref(**kwargs):
    ds = Dataset(**kwargs)
    ds_ref = DatasetRef(id=ds.id)
    return ds, ds_ref

def create_pixels(obj):
    # we're assuming a single Pixels object per image
    pix_obj = obj.getPrimaryPixels()
    pixels=Pixels(
        id='Pixels:0',
        dimension_order=pix_obj.getDimensionOrder().getValue(),
        size_c=pix_obj.getSizeC(),
        size_t=pix_obj.getSizeT(),
        size_x=pix_obj.getSizeX(),
        size_y=pix_obj.getSizeY(),
        size_z=pix_obj.getSizeZ(),
        type=pix_obj.getPixelsType().getValue(),
        metadata_only=True)
    return pixels

def create_image_and_ref(**kwargs):
    img = Image(**kwargs)
    img_ref = ImageRef(id=img.id)
    return img, img_ref

def create_tag_and_ref(ome, **kwargs):
    tag = TagAnnotation(**kwargs)
    tagref = AnnotationRef(id=tag.id)
    return tag, tagref

def create_kv_and_ref(ome, **kwargs):
    kv = MapAnnotation(**kwargs)
    kvref = AnnotationRef(id=kv.id)
    return kv, kvref

def populate_image(obj, ome, conn):
    id = obj.getId()
    name = obj.getName()
    desc = obj.getDescription()
    pix = create_pixels(obj)
    img, img_ref = create_image_and_ref(id=id, name=name, description=desc, pixels=pix)
    for ann in obj.listAnnotations():
        if ann.OMERO_TYPE == TagAnnotationI:
            tag, ref = create_tag_and_ref(ome, id=ann.getId(), value=ann.getTextValue())
            if tag not in ome.structured_annotations:
                ome.structured_annotations.append(tag)
            img.annotation_ref.append(ref)
        if ann.OMERO_TYPE == MapAnnotationI:
            kv, ref = create_kv_and_ref(ome, id=ann.getId(), value=Map(m=[M(k=_key, value=str(_value)) for _key, _value in ann.getMapValueAsMap().items()]))
            print(kv.value.m[0].k) # this is how you retrieve the key for the first kv pair in this annotation
            if kv not in ome.structured_annotations:
                ome.structured_annotations.append(kv)
            img.annotation_ref.append(ref)
    if img not in ome.images:
        ome.images.append(img)
    return img_ref


def populate_dataset(obj, ome, conn):
    id = obj.getId()
    name = obj.getName()
    desc = obj.getDescription()
    ds, ds_ref = create_dataset_and_ref(id=id, name=name, description=desc)
    for ann in obj.listAnnotations():
        if ann.OMERO_TYPE == TagAnnotationI:
            tag, ref = create_tag_and_ref(ome, id=ann.getId(), value=ann.getTextValue())
            if tag not in ome.structured_annotations:
                ome.structured_annotations.append(tag)
            ds.annotation_ref.append(ref)
        if ann.OMERO_TYPE == MapAnnotationI:
            kv, ref = create_kv_and_ref(ome, id=ann.getId(), value=Map(m=[M(k=_key, value=str(_value)) for _key, _value in ann.getMapValueAsMap().items()]))
            print(kv.value.m[0].k) # this is how you retrieve the key for the first kv pair in this annotation
            if kv not in ome.structured_annotations:
                ome.structured_annotations.append(kv)
            ds.annotation_ref.append(ref)
    for img in obj.listChildren():
        img_obj = conn.getObject('Image', img.getId())
        img_ref = populate_image(img_obj, ome, conn)
        ds.image_ref.append(img_ref)
    if ds not in ome.datasets:
        ome.datasets.append(ds)
    return ds_ref


def populate_project(obj, ome, conn):
    id = obj.getId()
    name = obj.getName()
    desc = obj.getDescription()
    test_proj, _ = create_proj_and_ref(id=id, name=name, description=desc)
    for ann in obj.listAnnotations():
        if ann.OMERO_TYPE == TagAnnotationI:
            tag, ref = create_tag_and_ref(ome, id=ann.getId(), value=ann.getTextValue())
            if tag not in ome.structured_annotations:
                ome.structured_annotations.append(tag)
            test_proj.annotation_ref.append(ref)
        if ann.OMERO_TYPE == MapAnnotationI:
            kv, ref = create_kv_and_ref(ome, id=ann.getId(), value=Map(m=[M(k=_key, value=str(_value)) for _key, _value in ann.getMapValueAsMap().items()]))
            print(kv.value.m[0].k) # this is how you retrieve the key for the first kv pair in this annotation
            if kv not in ome.structured_annotations:
                ome.structured_annotations.append(kv)
            test_proj.annotation_ref.append(ref)
    for ds in obj.listChildren():
        ds_obj = conn.getObject('Dataset', ds.getId())
        ds_ref = populate_dataset(ds_obj, ome, conn)
        test_proj.dataset_ref.append(ds_ref)
    ome.projects.append(test_proj)


def populate_xml(datatype, id, conn):
    ome = OME()
    obj = conn.getObject(datatype, id)
    if datatype == 'Project':
        populate_project(obj, ome, conn)
    

    # test_ds, test_ds_ref = create_dataset_and_ref(id=666, name='test_dataset', description='test dataset')
    # test_proj.dataset_ref.append(test_ds_ref)
    # ome.datasets.append(test_ds)

    # test_img, test_img_ref = create_image_and_ref(obj, id=420, name='this image')
    # test_ds.image_ref.append(test_img_ref)
    # ome.images.append(test_img)

    print(ome)
    print(to_xml(ome))
    return

if __name__ == "__main__":
    conn = ezomero.connect('root', 'omero', host='localhost', port=6064, group='system', secure=True)
    parser = argparse.ArgumentParser()
    parser.add_argument('datatype',
                        type=str,
                        help='Type of data (project, dataset, image) to be moved')
    parser.add_argument('id',
                        type=int,
                        help='ID of the data to be moved')
    args = parser.parse_args()

    populate_xml(args.datatype, args.id, conn)
    conn.close()