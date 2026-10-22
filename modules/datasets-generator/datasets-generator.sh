CI_PROJECT_DIR="${GITHUB_WORKSPACE:-$(pwd)}"

contents_dir_path=$CI_PROJECT_DIR/contents
persons_dir_path=$CI_PROJECT_DIR/persons
institutions_dir_path=$CI_PROJECT_DIR/institutions
places_dir_path=$CI_PROJECT_DIR/places
venues_dir_path=$CI_PROJECT_DIR/venues
events_dir_path=$CI_PROJECT_DIR/events
performanceEvents_dir_path=$CI_PROJECT_DIR/performanceEvents
instrumentations_dir_path=$CI_PROJECT_DIR/instrumentations
works_dir_path=$CI_PROJECT_DIR/works
expressions_dir_path=$CI_PROJECT_DIR/expressions
manifestations_dir_path=$CI_PROJECT_DIR/manifestations
items_dir_path=$CI_PROJECT_DIR/items
bibliography_dir_path=$CI_PROJECT_DIR/bibliography
letters_dir_path=$CI_PROJECT_DIR/letters
modules_dir_path=$CI_PROJECT_DIR/modules
datasets_generator_dir_path=$modules_dir_path/datasets-generator
public_dir_path=$CI_PROJECT_DIR/public
datasets_dir_path=$public_dir_path/datasets

mkdir -p $datasets_dir_path

echo "construct the persons dataset"
time /static-publishing-backend rdf-data-aggregator $persons_dir_path/ "*.ttl" $datasets_generator_dir_path/persons.sparql $datasets_dir_path/persons.ttl

echo "construct the institutions dataset"
time /static-publishing-backend rdf-data-aggregator $institutions_dir_path/ "*.ttl" $datasets_generator_dir_path/institutions.sparql $datasets_dir_path/institutions.ttl

echo "construct the places dataset"
time /static-publishing-backend rdf-data-aggregator $places_dir_path/ "*.ttl" $datasets_generator_dir_path/places.sparql $datasets_dir_path/places.ttl

echo "construct the venues dataset"
time /static-publishing-backend rdf-data-aggregator $CI_PROJECT_DIR/ "[vp]*/*.ttl" $datasets_generator_dir_path/venues.sparql $datasets_dir_path/venues.ttl

echo "construct the events dataset"
time /static-publishing-backend rdf-data-aggregator $events_dir_path/ "*.ttl" $datasets_generator_dir_path/events.sparql $datasets_dir_path/events.ttl

echo "construct the performance-events dataset"
time /static-publishing-backend rdf-data-aggregator $CI_PROJECT_DIR/ "p*/*.ttl" $datasets_generator_dir_path/performanceEvents.sparql $datasets_dir_path/performanceEvents.ttl

echo "construct the instrumentations dataset"
time /static-publishing-backend rdf-data-aggregator $instrumentations_dir_path/ "*.ttl" $datasets_generator_dir_path/instrumentations.sparql $datasets_dir_path/instrumentations.ttl

echo "construct the works dataset"
time /static-publishing-backend rdf-data-aggregator $CI_PROJECT_DIR/ "[wp]*/*.ttl" $datasets_generator_dir_path/works.sparql $datasets_dir_path/works.ttl

echo "construct the expressions dataset"
time /static-publishing-backend rdf-data-aggregator $expressions_dir_path/ "*.ttl" $datasets_generator_dir_path/expressions.sparql $datasets_dir_path/expressions.ttl

echo "construct the manifestations dataset"
time /static-publishing-backend rdf-data-aggregator $manifestations_dir_path/ "*.ttl" $datasets_generator_dir_path/manifestations.sparql $datasets_dir_path/manifestations.ttl

echo "construct the items dataset"
time /static-publishing-backend rdf-data-aggregator $items_dir_path/ "*.ttl" $datasets_generator_dir_path/items.sparql $datasets_dir_path/items.ttl

echo "construct the bibliography dataset"
time /static-publishing-backend rdf-data-aggregator $bibliography_dir_path/ "*.ttl" $datasets_generator_dir_path/bibliography.sparql $datasets_dir_path/bibliography.ttl

echo "construct the letters dataset"
time /static-publishing-backend rdf-data-aggregator $letters_dir_path/ "*.ttl" $datasets_generator_dir_path/letters.sparql $datasets_dir_path/letters.ttl
