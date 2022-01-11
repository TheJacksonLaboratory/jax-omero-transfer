import configparser
import argparse
import ezomero
import getpass
import ome_types
import os
import pwd
import grp
import sys
import subprocess
from collections import defaultdict
from pkg_resources import SOURCE_DIST
from generate_xml import populate_xml
from omero.sys import Parameters
from omero.rtypes import rstring
from generate_omero_objects import populate_omero

DIR_PERM = 0o755

def demote(user_uid, user_gid, homedir):
    def result():
        os.setgid(user_gid)
        os.setuid(user_uid)
        os.environ["HOME"] = homedir
    return result



def get_source_connection(config):
    SOURCE_OMERO_USER = config['source_omero']['user']
    SOURCE_OMERO_PASSWORD = config['source_omero'].get('password', None)
    SOURCE_OMERO_HOST = config['source_omero']['hostname']
    SOURCE_OMERO_PORT = int(config['source_omero']['port'])
    SOURCE_OMERO_GROUP = config['source_omero']['group']
    SOURCE_OMERO_SECURE = config['source_omero'].getboolean('secure')
    if SOURCE_OMERO_PASSWORD is not None:
        sourceconn = ezomero.connect(SOURCE_OMERO_USER, SOURCE_OMERO_PASSWORD,
                           host=SOURCE_OMERO_HOST, port=SOURCE_OMERO_PORT,
                           group=SOURCE_OMERO_GROUP, secure=SOURCE_OMERO_SECURE)
    else:
        src_pass = getpass.getpass(f'Password for user {SOURCE_OMERO_USER} on server {SOURCE_OMERO_HOST}:')
        sourceconn = ezomero.connect(SOURCE_OMERO_USER, src_pass,
                           host=SOURCE_OMERO_HOST, port=SOURCE_OMERO_PORT,
                           group=SOURCE_OMERO_GROUP, secure=SOURCE_OMERO_SECURE)
    return sourceconn

def get_destination_connection(config):
    DEST_OMERO_USER = config['dest_omero']['user']
    DEST_OMERO_PASSWORD = config['dest_omero'].get('password', None)
    DEST_OMERO_HOST = config['dest_omero']['hostname']
    DEST_OMERO_PORT = int(config['dest_omero']['port'])
    DEST_OMERO_GROUP = config['dest_omero']['group']
    DEST_OMERO_SECURE = config['dest_omero'].getboolean('secure')
    if DEST_OMERO_PASSWORD is not None:
        destconn = ezomero.connect(DEST_OMERO_USER, DEST_OMERO_PASSWORD,
                           host=DEST_OMERO_HOST, port=DEST_OMERO_PORT,
                           group=DEST_OMERO_GROUP, secure=DEST_OMERO_SECURE)
    else:
        dest_pass = getpass.getpass(f'Password for user {DEST_OMERO_USER} on server {DEST_OMERO_HOST}:')
        destconn = ezomero.connect(DEST_OMERO_USER, dest_pass,
                           host=DEST_OMERO_HOST, port=DEST_OMERO_PORT,
                           group=DEST_OMERO_GROUP, secure=DEST_OMERO_SECURE)
    return destconn


def list_source_files(xml_file, client_fps, managedrepo_dir, conn):
    # go through all images in XML, create list of filepaths.
    # return both a map between files and IDs and a simple list of files
    filelist = []
    file_img_tuples = []
    ome = ome_types.from_xml(xml_file)
    for img in ome.images:
        img_id = int(img.id.split(':')[-1])
        if client_fps:
            img_files = ezomero.get_original_filepaths(conn, img_id, fpath='client')
        else:
            img_files = ezomero.get_original_filepaths(conn, img_id)
        for f in img_files:
            f = str(os.path.join(managedrepo_dir, f))
            file_img_tuples.append((f, img_id))
            filelist.append(f)
    d = defaultdict(list)
    for k, v in file_img_tuples:
        d[k].append(v)
    d = {x:sorted(d[x]) for x in d.keys()}
    filelist = (list(set(filelist)))
    return d, filelist

def copy_files(filelist, source_user, source_host, dest_user, dest_group, dest_dir):
    # copy files between servers (scp?) using the correct users
    # note that this flattens the dir structure, so if multiple source-side files
    # have the same filename, this is a problem
    source_user_uid = pwd.getpwnam(dest_user).pw_uid
    data_user_gid = grp.getgrnam(dest_group).gr_gid
    data_user_home = f"/home/{dest_user}"
    os.makedirs(dest_dir, mode=DIR_PERM, exist_ok=True)
    copycmd = ['scp', '-T', source_user+"@"+source_host+":"+" ".join(filelist),
                dest_dir+"/"]
    process = subprocess.Popen(copycmd,
                            preexec_fn=demote(source_user_uid,
                                                data_user_gid,
                                                data_user_home),
                            stdout=sys.stdout,
                            stderr=sys.stderr
                            )
    process.communicate()
    return 

def get_image_ids(file_path, destconn):
        """Get the Ids of imported images.
        Note that this will not find images if they have not been imported.
        
        Returns
        -------
        image_ids : list of ints
            Ids of images imported from the specified client path, which
            itself is derived from ``file_path``.
        """
        
        q = destconn.getQueryService()
        params = Parameters()
        path_query = str(file_path).strip('/')
        params.map = {"cpath": rstring(path_query)}
        results = q.projection(
            "SELECT i.id FROM Image i"
            " JOIN i.fileset fs"
            " JOIN fs.usedFiles u"
            " WHERE u.clientPath=:cpath",
            params,
            destconn.SERVICE_OPTS
            )
        image_ids = sorted([r[0].val for r in results])
        return image_ids

def import_files(dir, filelist, ln_s, destconn, host, port):
    # import destination-side files as orphans
    # create a map between files and image IDs
    session = destconn.getSession().getUuid().val
    dest_map = {}
    for file in filelist:
        dest_path = os.path.join(dir, os.path.basename(file))
        if ln_s:
            import_cmd = ['omero', 'import', '-k', session, '-s', host, '-p', str(port), 
                          '--transfer', 'ln_s', str(dest_path)]
        else:
            import_cmd = ['omero', 'import', '-k', session, '-s', host, '-p', str(port), 
                          str(dest_path)]
        print(import_cmd)
        process = subprocess.Popen(import_cmd,
                            stdout=sys.stdout,
                            stderr=sys.stderr
                            )
        process.communicate()

        img_ids = get_image_ids(dest_path, destconn)
        dest_map[dest_path] = img_ids
    return dest_map

def make_image_map(source_map, dest_map):
    # using both source and destination file-to-image-id maps,
    # map image IDs between source and destination
    src_dict = defaultdict(list)
    imgmap = {}
    for k, v in source_map.items():
        newkey = os.path.basename(k)
        src_dict[newkey].extend(v)
    dest_dict = defaultdict(list)
    print(src_dict)
    for k, v in dest_map.items():
        newkey = os.path.basename(k)
        dest_dict[newkey].extend(v)
    print(dest_dict)
    for src_k in src_dict.keys():
        src_v = src_dict[src_k]
        dest_v = dest_dict[src_k]
        for count in range(len(src_v)):
            map_key = f"Image:{src_v[count]}"
            imgmap[map_key] = dest_v[count]
    return imgmap


def main(configfile):
    config = configparser.ConfigParser()
    config.read(configfile)

    
    sourceconn = get_source_connection(config)

    SOURCE_DATA_TYPE = config['source_omero']['datatype']
    SOURCE_DATA_ID = config['source_omero']['id']
    XML_FILEPATH = config['general']['xml_filepath']
    SOURCE_CLIENT_FPS = config['source_omero'].getboolean('use_client_filepaths', False)
    print("Populating xml...")
    populate_xml(SOURCE_DATA_TYPE, SOURCE_DATA_ID, XML_FILEPATH, sourceconn)
    print(f"XML saved at {XML_FILEPATH}.")

    print("Listing source files...")
    MANAGED_REPO_DIR = config['source_server']['managedrepo_dir']
    src_file_id_map, filelist = list_source_files(XML_FILEPATH, SOURCE_CLIENT_FPS, MANAGED_REPO_DIR, sourceconn)
    sourceconn.close()

    print("Starting file copy...")
    SOURCE_USER = config['source_server']['user']
    DEST_USER = config['dest_server']['user']
    DEST_GROUP = config['dest_server']['group']
    DEST_DIRECTORY = config['dest_server']['data_directory']
    SOURCE_DATA_HOST = config['source_omero']['hostname']
    copy_files(filelist, SOURCE_USER, SOURCE_DATA_HOST, DEST_USER, DEST_GROUP, DEST_DIRECTORY)

    print("Importing files...")
    destconn = get_destination_connection(config)
    LN_S_IMPORT = config['general'].getboolean('ln_s_import')
    DEST_OMERO_HOST = config['dest_omero']['hostname']
    DEST_OMERO_PORT = int(config['dest_omero']['port'])
    dest_file_id_map = import_files(DEST_DIRECTORY, filelist, LN_S_IMPORT, destconn, DEST_OMERO_HOST, DEST_OMERO_PORT)
    img_map = make_image_map(src_file_id_map, dest_file_id_map)
    destconn = get_destination_connection(config)
    print("Creating and linking OMERO objects...")
    populate_omero(XML_FILEPATH, img_map, destconn)
    destconn.close()
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('filepath',
                        type=str,
                        help='filepath to load config file')
    args = parser.parse_args()
    main(args.filepath)
    