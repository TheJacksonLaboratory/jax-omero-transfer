import ezomero
import argparse
from ome_types import from_xml

def create_projects(pjs, conn):
    for pj in pjs:
        print(pj)

def create_datasets(dss, conn):
    return

def create_annotations(ans, conn):
    return

def create_rois(rois, imgs, img_map, conn):
    return

def link_datasets(ome, proj_map, ds_map, conn):
    return

def link_images(ome, ds_map, img_map, conn):
    return

def link_annotations(ome, proj_map, ds_map, img_map, conn):
    return

def populate_omero(fp, conn, img_map):
    ome = from_xml(fp)
    proj_map = create_projects(ome.projects, conn)
    ds_map = create_datasets(ome.datasets, conn)
    ann_map = create_annotations(ome.structured_annotations, conn)
    create_rois(ome.rois, ome.images, img_map, conn)
    link_datasets(ome, proj_map, ds_map, conn)
    link_images(ome, ds_map, img_map, conn)
    link_annotations(ome, proj_map, ds_map, img_map, conn)

    return

if __name__ == "__main__":
    conn = ezomero.connect('root', 'omero', host='localhost', port=6064, group='system', secure=True)
    parser = argparse.ArgumentParser()
    parser.add_argument('filepath',
                        type=str,
                        help='filepath to save xml')
    args = parser.parse_args()
    image_map = {51:1401, 52:1402, 27423:1403}
    populate_omero(args.filepath, conn, image_map)
    conn.close()