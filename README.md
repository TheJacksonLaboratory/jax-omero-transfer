# jax-omero-transfer
Transfer OMERO datsets from the Research server to the Public server.


# The Transfer Problem 

 

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
