from ome_types import to_xml, OME
from ome_types.model import Project, Dataset, Image, DatasetRef

ome = OME()
test_proj = Project(id=49, name='test_project', description='this is a test project')
ome.projects.append(test_proj)

test_ds = Dataset(id=666, name='test_dataset', description='test dataset')
test_ds_ref = DatasetRef(id=test_ds.id)
test_proj.dataset_ref.append(test_ds_ref)
ome.datasets.append(test_ds)

print(ome)
print(to_xml(ome))