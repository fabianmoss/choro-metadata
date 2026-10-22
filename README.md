# MerMEId template

> **Data repository of the Casa do Choro acervo.**
>
> This instance of the MerMEId MeLODy template models the acervo of the
> [Casa do Choro](https://acervo.casadochoro.com.br/).  The entities follow
> the FRBR chain (work → expression → manifestation → item), the people are
> Persons and the places are Places.  The mapping — and the decisions taken
> at each point — is described in
> [docs/acervo-model.md](docs/acervo-model.md).

This is the template repository, which can be used to create a new data repository to edit your own data in the [MerMEId MeLODy Editor](https://music-metadata-tools.github.io/MerMEId-MeLODy/).
It contains some example Turtle files and a datasets generator to create the indexes for the dropdown menus and search indexes, which are loaded in the editor.

To configure this repository, you need to activate the GitHub Pages and modify the configuration.


## 1. Set up GitHub Pages

After creating the data repository, activate GitHub Pages by going to Settings → Pages and setting the source to GitHub Actions.

## 2. Modify configuration file

To use the indexes in the editor, the correct url to the datasets needs to be modified in the [configuration.json file](configuration/config.json).
To do this, you need to replace the line 
```"datasetBaseUrl": "https://music-metadata-tools.github.io/MerMEId-MeLODy-Template/datasets/",``` 
to 
```"datasetBaseUrl": "{your_pages_url}/datasets/",```.

You can find your GitHub Pages url on the main site of your repository once the workflows for the GitHub Pages are activated

## Datasets generation

The GitHub Pages workflow generates the datasets (the indexes the editor
loads) from the SPARQL modules in `modules/datasets-generator`.  The same
generation can be run locally, without the container the CI uses, with:

```bash
pip install rdflib
python3 -m tools.datasets --out indexes
```

The `indexes/` folder keeps a copy of the generated datasets, so that the
dropdowns can be inspected without running the container.  It is also part of
the validation: the shapes reference the entities by the derived types of the
indexes (`melod:PersonEntity`…), and `npm test` mirrors the editor, which
validates a document against the shapes plus the indexes.  Regenerate the
indexes whenever you change entity documents.

### One entity type per document

Every entity document declares exactly one type: the base class of the
ontology, for instance `a melod:Expression`.  The editor refuses to open a
document with two types on the entity IRI, and the `*Entity` classes belong to
the generated indexes only.  `npm test` enforces this contract as well; see
§ 4.12 of [docs/acervo-model.md](docs/acervo-model.md).


## Data Validation

You can validate your data against the MerMEId MeLODy SHACL shapes using either:

### GitHub Actions Validation
1. Go to the "Actions" tab in your repository
2. Select "Data Validation" from the left sidebar
3. Click "Run workflow" button
4. View validation results in the workflow output


### Local Validation

For this you need node.js on your local machine.

1. Clone Repository
1. Install dependencies: `npm install`
2. Run validation: `npm test`

Validation will check all `.ttl` files in your data folders against the appropriate SHACL shapes and report any violations.