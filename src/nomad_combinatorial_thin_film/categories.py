from nomad.datamodel.data import EntryDataCategory
from nomad.metainfo.metainfo import Category


class Uppsala(EntryDataCategory):
    m_def = Category(label="Uppsala's custom schemas", categories=[EntryDataCategory])
