# MerMEId template

This is the template repository, which can be used to create a new data repository to edit your own data in the [MerMEId MeLODy Editor](https://music-metadata-tools.github.io/MerMEId-MeLODy/).
It contains some example Turtle files and a datasets generator to create the indexes for the dropdown menus and search indexes, which are loaded in the editor.

To configure this repository, you need to activate the GitHub Pages and modify the configuration.


## 1. Set up GitHub Pages

After creating the data repository, activate GitHub Pages by going to Settings → Pages and setting the source to GitHub Actions.

## 2. Modify configuration file

To use the indexes in the editor, the correct url to the datasets needs to be modified in the [configuration.json file](configuration/configuration.json).
To do this, you need to replace the line 
```"datasetBaseUrl": "https://music-metadata-tools.github.io/MerMEId-MeLODy-Template/datasets/",``` 
to 
```"datasetBaseUrl": "{your_pages_url}/datasets/",```.

You can find your GitHub Pages url on the main site of your repository once the workflows for the GitHub Pages are activated


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