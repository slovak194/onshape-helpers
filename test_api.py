# %%

import json

from onshape_client import OnshapeElement, Client
from onshape_client.oas.models.bt_configuration_params import BTConfigurationParams
from onshape_client.oas.models.configuration_entry import ConfigurationEntry


class OnshapeWrapper:
    def __init__(self, config_file=""):
        config_file = config_file
        self.client = Client(keys_file=config_file)

    @staticmethod
    def dweid_from_url(url):
        element = OnshapeElement(url)
        return element.did, element.wvmid, element.eid

    def dweid_from_names(self, document_name, element_name):
        documents = self.client.documents_api.get_documents(filter=0)
        document = list(filter(lambda x: x["name"] == document_name, documents["items"]))[0]

        workspaces = self.client.documents_api.get_document_workspaces(document["id"])
        workspace = workspaces[0]

        elements = self.client.documents_api.get_elements_in_document(document["id"], "w", workspace["id"])
        element = list(filter(lambda x: x["name"] == element_name, elements))[0]

        did = document["id"]
        wid = workspace["id"]
        eid = element["id"]

        return did, wid, eid

    def store_stl_from_url(self, url="", path="", part_names="", confdict=None, **kwargs):
        ids = self.dweid_from_url(url)
        self.store_stl(ids, path=path, part_names=part_names, confdict=confdict, **kwargs)

    def store_stl_from_names(self, document_name="", element_name="", path="", part_names="", confdict=None, **kwargs):
        ids = self.dweid_from_names(document_name, element_name)
        self.store_stl(ids, path=path, part_names=part_names, confdict=confdict, **kwargs)

    def store_stl(self, ids, path="", part_names="", confdict=None, **kwargs):

        did, wid, eid = ids

        if confdict is not None:
            kwargs["configuration"] = self.build_config_string(did, eid, confdict)

        parts = self.client.parts_api.get_parts_wmve(did, "w", wid, eid)

        if isinstance(part_names, str) and len(part_names) != 0:
            part_names = [part_names]

        if isinstance(part_names, str) and len(part_names) == 0:
            part_names = [part["name"] for part in parts]

        for part_name in part_names:
            part = list(filter(lambda x: x["name"] == part_name, parts))[0]

            response = self.client.part_studios_api.export_stl1(
                did, 'w', wid, eid,
                part_ids=part["part_id"], _preload_content=False, units="millimeter", **kwargs
            )

            file_name = path + '{}.stl'.format(part["name"])

            with open(file_name, 'wb') as f:
                f.write(response.data)

            print("--> " + file_name)

    def build_config_string(self, did, eid, confdict):
        params = BTConfigurationParams(parameters=[ConfigurationEntry(parameter_id=k, parameter_value=v) for k, v in confdict.items()])
        r = self.client.elements_api.encode_configuration_map(did, eid, params, _preload_content=False)
        return json.loads(r.data.decode("UTF-8"))["encodedId"]


# %%

osh = OnshapeWrapper(config_file="/home/slovak/onshape/onshape_client_config.yaml")

# %%

osh.store_stl_from_url(
    url="https://cad.onshape.com/documents/ca8f441b906a5949eb4e8196/w/3ffa603f8af8def1150f37d7/e/6f99613c6b7785778f175123",
    part_names="",
    confdict={"L": "0.05 m"}
)

# %%
osh.store_stl_from_names(
    document_name="HomePrints",
    element_name="TovelHolder",
    part_names=""
)

# %%

import json

did, wid, eid = osh.dweid_from_url("https://cad.onshape.com/documents/ca8f441b906a5949eb4e8196/w/3ffa603f8af8def1150f37d7/e/6f99613c6b7785778f175123")

conf = osh.client.elements_api.get_configuration(did, "w", wid, eid, _preload_content=False)

res = json.loads(conf.data)
res["configurationParameters"][0]["message"]["rangeAndDefault"]["message"]["defaultValue"] = 2.0

