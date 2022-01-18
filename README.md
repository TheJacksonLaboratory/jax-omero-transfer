# jax-omero-transfer
Transfer OMERO datsets from the Research server to the Public server.

## What is this?

This is a prototype Python project to transfer _something_ between two OMERO servers. It takes the following steps:
- Constructs a XML document for the desired Project, Dataset or Image, specifiying all links between objects and annotations;
- Lists all necessary image files that need to be transfered between servers to reproduce the desired items;
- `rsync`s the files between the source server and your local machine (that is, hopefully, the destination server);
- Imports the files destination-side as orphans;
- Uses the generated XML to reproduce the links that existed originally.

This is a VERY limited tool right now - we would love to have more people contributing to it, be it through suggestions/issues but, most importantly, with PRs!

## Requirements

You need to have the python packages in `requirements.txt` installed, plus `rsync` installed at system level.

## Recommended workflow

We recommend running this prototype on your destination OMERO server. A simple `python transfer_workflow.py config.cfg` will do! Note that if the local user you are using to store the data requires you to have elevated privileges to switch to, you will need to `sudo`-run this.

## The config file

You need to pass a config file to `transfer_workflow.py`. We provide an example with the repo. A quick explanation about the options there:

1) [source_omero]: `hostname, port, group, user, password, secure` are all options for your connection to the OMERO server (`password` is optional - if you do not want to store it in plain text on the config file **(and you shouldn't)**, it will prompt you for a password when running it). `datatype` is one of Project, Dataset or Image (note the capitalization!), and `id` specifies the ID of the datatype to be transfered (so `Project` and `51` for these two options will transfer Project with ID 51 between servers). `use_client_filepaths` specifies whether to use client filepaths to retrieve the files from the source server.
2) [dest_omero]: `hostname, port, group, user, password, secure` are all options for your connection to the OMERO server (`password` is optional - if you do not want to store it in plain text on the config file **(and you shouldn't)**, it will prompt you for a password when running it).
3) [source_server]: `user` and `hostname` will be used to connect to the source server at filesystem-level to transfer files (note that storing THIS password in clear text here is not an option). `managedrepo_dir` is the full path to the `ManagedRepository` directory in this server, where we will find the original imported files.
4) [data_storage]: `user` and `group` are the **local** users that will be used to store the data **locally**, and `data_directory` is where you are going to put the original image files locally. 
5) [general]: `xml_filepath` is the path where you are going to store the XML describing all links between objects. `ln_s_import` is whether you want to import files using the `ln_s` option for in-place importing. Note that this option only works if you are running this on the destination server!

## Caveats, warnings, limitations

- Starting with the obvious: **this is a prototype, it is in development, and it has no warranties**. Use at your own risk. This has a lot of moving parts, interacting with multiple machines both at OMERO and filesystem level. It can break in thousands of different ways, and there is no easy way to thoroughly test it. We do not recommend using this if you are not proficient with Python, and a seasoned OMERO veteran. 
- For the moment, we are only dealing with Tags, Map Annotations and ROIs. No File Annotations, ratings, comments, etc. These are all feasible, we just decided to focus on the basic stuff first.
- We do not know how to deal with Plates and Screens right now. Sorry.
- We are also not dealing with images without underlying files right now (i.e. created using `Pixels`). 
- ROIs are limited to `ezomero.rois` types (Point, Ellipse, Rectangle, Line, Polygon). All other ROIs will be skipped.
- We assume Bioformats generates Image IDs in the same order for the same files (which is relevant for multi-series file formats).
- OMERO does some strange setting with channel = -1 for ROIs sometimes (for RGB images, I think).  `ome-types` hates that, so we set those values to 0.
- `ome-types` also doesn't like empty values on MapAnnotations, so we're working around it by adding a single space as a value.

  \
  \
  \
&nbsp;


# Extra reading: The Transfer Problem 

## Scenario 1: “simple” solution for limited use cases 

- Traverse origin project/dataset/list of images. For each image: 
    - Note project/dataset where it is 
    - Retrieve which Fileset it belongs to 
    - Retrieve existing ROI and MapAnnotation contents 
    - Note which Tags are attached to it 
- Make comprehensive list of all Filesets that need transferring and Tags that need recreating 
- Move Filesets between servers and create import JSON file with Project, Dataset and MapAnnotations 
- Import data destination-side using import JSON 
- Recreate relevant tags and link them to the correct images 
- Post ROIs to each image 
- Data to be transferred: Filesets, import JSON, ROI JSON, Tags JSON 

**Alternative:** use ome-types and work with XML instead 

**Issues:** How do we identify images one-to-one between source and destination? How do we rely on ID ordering for Fileset importing? Non-custom image names? Is there some “import name” property buried deep into the OMERO DB that could save us here? 

**Caveats:** 

- Filesets need to be transferred whole 
- MapAnnotations and ROIs are transferred in content only; no specific graph connectivity is guaranteed (i.e. if you had the same MapAnnotation or ROI linked to multiple images, it will be transferred as multiple identical instances) 

 


## Scenario 2: more extensive ezomero-based solution 

- Basically like scenario 1, but more comprehensive in what it moves over: FileAnnotations, comments, ratings, etc etc 
- Basic functionality is the same, but we would have extra JSON files for each type of Annotation and/or extra fields in the import JSON 
- Files attached to FileAnnotations would also need to be copied 
- Issues and caveats are still pretty similar to scenario 1 




## Scenario 3: JSON-LD “complete” solution 

- List and traverse whole Filesets as a starting point? 
- Create graph edges in JSON-LD 
- List all nodes at source, recreate nodes at destination 
- Create all links specified on JSON-LD 

Caveats/Issues 

- Is the image identification problem still an issue? 
- How deep do we go graph-wise? 
- Data reimport is still necessary on the destination, right? So anything generated at import time doesn’t need to be captured on the JSON file 
- Is a reimport-less workflow even possible?

## Questions about ome-types approach
- Do we need to map image IDs across servers or can the xml itself be used to manage the import?
- Do we need to think differently about how to handle plates (e.g., Project/Dataset has no meaning for plate data)
