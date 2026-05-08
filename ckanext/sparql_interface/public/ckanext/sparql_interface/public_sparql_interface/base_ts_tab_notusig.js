var $ = jQuery.noConflict();

$('#sparql_results').hide();
$('#sparql_link_query').hide();
$('#loading_image').hide();

var prefixes = "PREFIX void: <http://rdfs.org/ns/void#> PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#> PREFIX foaf: <http://xmlns.com/foaf/0.1/> PREFIX vann: <http://purl.org/vocab/vann/> PREFIX teach: <http://linkedscience.org/teach/ns#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX dcat: <http://www.w3.org/ns/dcat#> PREFIX crsw: <http://courseware.rkbexplorer.com/ontologies/courseware#> PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> PREFIX owl: <http://www.w3.org/2002/07/owl#> PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> PREFIX aiiso: <http://purl.org/vocab/aiiso/schema#> PREFIX univcat: <http://data.upf.edu/upf/ontologies/universidadcatalana#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX vivo: <http://vivoweb.org/ontology/core#> PREFIX sbench: <http://swat.cse.lehigh.edu/onto/univ-bench.owl#> PREFIX sdmx-attribute: <http://purl.org/linked-data/sdmx/2009/attribute#> PREFIX sdmx-concept: <http://purl.org/linked-data/sdmx/2009/concept#> PREFIX sdmx-code: <http://purl.org/linked-data/sdmx/2009/code#> PREFIX disco: <http://rdf-vocabulary.ddialliance.org/discovery#> PREFIX sdmx-dimension: <http://purl.org/linked-data/sdmx/2009/dimension#> PREFIX sdmx-measure: <http://purl.org/linked-data/sdmx/2009/measure#> PREFIX qb: <http://purl.org/linked-data/cube#> PREFIX sdmx: <http://purl.org/linked-data/sdmx#>";

var editorCount = 0;
var editors = {};
var currentTabId = null;

$(document).ready(function() {
    // Add initial tab
    createNewTab();

    // Event listener for the "Title & Description" button
    $('button#title_with_inchi').on('click', function(e) {
        e.preventDefault();  // Prevent default form submission if the button is inside a form
        createInchiTab();
    });

    // Event listener for the "Fed Query with Wiki" button
    $('button#find_datasets_by_ikey').on('click', function(e) {
        e.preventDefault();  // Prevent default form submission if the button is inside a form
        createFedOrkgTab();
    });

    // Event listener for the "Number Of datasets" button
    $('button#nr_of_datasets').on('click', function(e) {
        e.preventDefault();  // Prevent default form submission if the button is inside a form
        createNrDatasets();
    });

    // Event listener for adding a new tab
    $('#add_tab').on('click', function() {
        createNewTab();
    });

    // Check for 'view_code' parameter in the URL and set it in the editor
    var sparql_query = GetURLParameter('view_code');
    if (sparql_query != "" && sparql_query != undefined) {
        editors[currentTabId].setValue(decodeURIComponent((sparql_query + '').replace(/\+/g, '%20')));
    }
});

// Function to create a new tab
function createNewTab(tabName = `Query ${editorCount + 1}`) {
    editorCount++;
    const tabId = 'editor' + editorCount;

    // Create tab button with an 'x' for closing inside the same div
    const tabButton = $('<div class="btn-group tab-class me-1" role="group" aria-label="Basic radio toggle button group"></div>')
        .append($('<button type="button" class="btn custom-btn"></button>')
            .text(tabName)
            .attr('data-tab-id', tabId)
            .on('click', function() {
                switchTab(tabId);
            })
            .on('dblclick', function() {
                renameTab(this);
            })
        )
        .append($('<span class="btn btn-outline-success">x</span>')
            .on('click', function(e) {
                e.stopPropagation();
                removeTab(tabId);
            })
        );

    $('#tabs_container').append(tabButton);

    // Create a new div for the editor
    const editorDiv = $('<div></div>').attr('id', tabId).css('display', 'none');
    $('#editors_container').append(editorDiv);

    let editor;
    if (editorCount === 1) {
        // Initialize CodeMirror on the existing <textarea> for the first tab
        editor = CodeMirror.fromTextArea(document.getElementById('sparql_code'), {
            mode: "application/x-sparql-query",
            lineNumbers: true
        });
    } else {
//        // Create a new empty textarea for subsequent tabs
//        const textarea = $('<textarea></textarea>')
//            .attr('id', 'sparql_code_' + editorCount)
//            .css({
//                'width': '100%',
//                'height': '300px'
//            });
//        editorDiv.append(textarea);

        // Initialize CodeMirror on the new empty textarea
        editor = CodeMirror.fromTextArea(document.getElementById('sparql_code_open'), {
            mode: "application/x-sparql-query",
            lineNumbers: true
        });
    }

    editorDiv.append(editor.getWrapperElement());
    editors[tabId] = editor;

    // Switch to the new tab
    switchTab(tabId);
}

// Function to create a new tab specifically for 'title_with_inchi'
function createInchiTab() {
    // Check if a tab with this name already exists
    if ($('[data-tab-id="title_with_inchi_tab"]').length > 0) {
        switchTab('title_with_inchi_tab');  // Switch to the existing tab if it exists
        return;
    }

    editorCount++;
    const tabId = 'title_with_inchi_tab';

    // Create tab button with an 'x' for closing
    const tabButton = $('<div class="btn-group tab-class me-1" role="group" aria-label="Basic radio toggle button group"></div>')
        .append($('<button type="button" class="btn custom-btn"></button>')
            .text('Title & Description')
            .attr('data-tab-id', tabId)
            .on('click', function() {
                switchTab(tabId);
            })
            .on('dblclick', function() {
                renameTab(this);
            })
        )
        .append($('<span class="btn btn-outline-success">x</span>')
            .on('click', function(e) {
                e.stopPropagation();
                removeTab(tabId);
            })
        );

    $('#tabs_container').append(tabButton);

    // Create a new div for the editor
    const editorDiv = $('<div></div>').attr('id', tabId).css('display', 'none');
    $('#editors_container').append(editorDiv);

    // Initialize CodeMirror on the 'title_with_inchi' <textarea>
    const editor = CodeMirror.fromTextArea(document.getElementById('title_with_inchi_text'), {
        mode: "application/x-sparql-query",
        lineNumbers: true
    });

    editorDiv.append(editor.getWrapperElement());
    editors[tabId] = editor;

    // Switch to the new tab
    switchTab(tabId);
}

function createFedOrkgTab() {
    // Check if a tab with this name already exists
    if ($('[data-tab-id="find_datasets_by_ikey_tab"]').length > 0) {
        switchTab('find_datasets_by_ikey_tab');  // Switch to the existing tab if it exists
        return;
    }

    editorCount++;
    const tabId = 'find_datasets_by_ikey_tab';

    // Create tab button with an 'x' for closing
    const tabButton = $('<div class="btn-group tab-class me-1" role="group" aria-label="Basic radio toggle button group"></div>')
        .append($('<button type="button" class="btn custom-btn"></button>')
            .text('Fed Query with Wiki')
            .attr('data-tab-id', tabId)
            .on('click', function() {
                switchTab(tabId);
            })
            .on('dblclick', function() {
                renameTab(this);
            })
        )
        .append($('<span class="btn btn-outline-success">x</span>')
            .on('click', function(e) {
                e.stopPropagation();
                removeTab(tabId);
            })
        );

    $('#tabs_container').append(tabButton);

    // Create a new div for the editor
    const editorDiv = $('<div></div>').attr('id', tabId).css('display', 'none');
    $('#editors_container').append(editorDiv);

    // Initialize CodeMirror on the 'title_with_inchi' <textarea>
    const editor = CodeMirror.fromTextArea(document.getElementById('find_datasets_by_ikey_text'), {
        mode: "application/x-sparql-query",
        lineNumbers: true
    });

    editorDiv.append(editor.getWrapperElement());
    editors[tabId] = editor;

    // Switch to the new tab
    switchTab(tabId);
}


function createNrDatasets() {
    // Check if a tab with this name already exists
    if ($('[data-tab-id="nr_of_datasets_tab"]').length > 0) {
        switchTab('nr_of_datasets_tab');  // Switch to the existing tab if it exists
        return;
    }

    editorCount++;
    const tabId = 'nr_of_datasets_tab';

    // Create tab button with an 'x' for closing
    const tabButton = $('<div class="btn-group tab-class me-1" role="group" aria-label="Basic radio toggle button group"></div>')
        .append($('<button type="button" class="btn custom-btn"></button>')
            .text('Nr. of Datasets')
            .attr('data-tab-id', tabId)
            .on('click', function() {
                switchTab(tabId);
            })
            .on('dblclick', function() {
                renameTab(this);
            })
        )
        .append($('<span class="btn btn-outline-success">x</span>')
            .on('click', function(e) {
                e.stopPropagation();
                removeTab(tabId);
            })
        );

    $('#tabs_container').append(tabButton);

    // Create a new div for the editor
    const editorDiv = $('<div></div>').attr('id', tabId).css('display', 'none');
    $('#editors_container').append(editorDiv);

    // Initialize CodeMirror on the 'title_with_inchi' <textarea>
    const editor = CodeMirror.fromTextArea(document.getElementById('nr_of_datasets_text'), {
        mode: "application/x-sparql-query",
        lineNumbers: true
    });

    editorDiv.append(editor.getWrapperElement());
    editors[tabId] = editor;

    // Switch to the new tab
    switchTab(tabId);
}

// Function to switch between tabs
function switchTab(tabId) {
    if (currentTabId) {
        $('#' + currentTabId).hide();
        $('[data-tab-id="' + currentTabId + '"]').removeClass('active');
    }
    currentTabId = tabId;
    $('#' + tabId).show();
    $('[data-tab-id="' + tabId + '"]').addClass('active');
}

// Function to remove a tab
function removeTab(tabId) {
    if (currentTabId === tabId) {
        $('#' + tabId).hide();
        const remainingTabs = Object.keys(editors).filter(id => id !== tabId);
        if (remainingTabs.length > 0) {
            switchTab(remainingTabs[0]);
        } else {
            currentTabId = null;
        }
    }
    $('#' + tabId).remove();
    $('[data-tab-id="' + tabId + '"]').closest('.btn-group').remove();
    delete editors[tabId];
}

// Function to rename a tab
function renameTab(tabElement) {
    const newName = prompt("Enter new name for the tab:", $(tabElement).text());
    if (newName) {
        $(tabElement).text(newName);
    }
}

// Helper function to get URL parameters
function GetURLParameter(sParam) {
    var sPageURL = window.location.search.substring(1);
    var sURLVariables = sPageURL.split('&');
    for (var i = 0; i < sURLVariables.length; i++) {
        var sParameterName = sURLVariables[i].split('=');
        if (sParameterName[0] == sParam) {
            return sParameterName[1];
        }
    }
    return null;
}

// Function to call the SPARQL point server and display the results
function call_sparql_point_server() {
    if ($("#field-sparql-server").val().length == 0) {
        $('#loading_image').hide();
        $('#sparql_results').show();
        $('#sparql_results').html("<div class='alert alert-error'><a href='#' class='close' data-dismiss='alert'>&times;</a><strong>Error: </strong>Please add the Sparql Point Server URL. For Instance: http://semantic.ckan.net/sparql. </div>");
        return;
    }

    $('#sparql_results').html("");
    $('#go_to_link_query').attr("href", '');
    $('#field-link-sparql-server-query').val('');
    $('#sparql_link_query').hide();
    $('#sparql_results').hide();
    $('#loading_image').show();

    $.ajax({
        type: 'GET',
        url: 'sparql_interface/query',
        data: {
            'query': prefixes + get_sparql_string(),
            'server': $("#field-sparql-server").val(),
            'direct_link': 0
        },
        success: function(response) {
            $('#sparql_results').html(response);

            var base_address = queryHref() + '/' + change_direct_link_value(this.url);

            $('#field-link-sparql-server-query_json').val(base_address + add_extra_fields_url('json'));
            $('#go_to_link_query_json').attr("href", base_address + add_extra_fields_url('json'));

            $('#field-link-sparql-server-query_turtle').val(base_address + add_extra_fields_url('turtle'));
            $('#go_to_link_query_turtle').attr("href", base_address + add_extra_fields_url('turtle'));

            $('#field-link-sparql-server-query_csv').val(base_address + add_extra_fields_url('csv'));
            $('#go_to_link_query_csv').attr("href", base_address + add_extra_fields_url('csv'));

            $('#go_to_link_query_query').attr("href", window.location.pathname + '?' + $.param({
                'view_code': prefixes + editors[currentTabId].getValue()
            }));

            $('#sparql_results').show();
            $('#sparql_link_query').show();
            $('#loading_image').hide();
        },
        error: function(request, status, error) {
            $('#loading_image').hide();
            $('#sparql_results').show();
            $('#sparql_results').html("<div class='alert alert-error'><a href='#' class='close' data-dismiss='alert'>&times;</a><strong>Error: </strong>Please Verify your query. </div>");
            return;
        }
    });
}

function change_direct_link_value(url) {
    var new_url = url.substring(0, url.length - 1);
    return new_url + '1';
}

function add_extra_fields_url(field) {
    var sparql_extra_fields = '';
    if (field == 'json')
        sparql_extra_fields = '&type_response_query=json';
    else if (field == 'turtle')
        sparql_extra_fields = '&type_response_query=turtle';
    else if (field == 'csv')
        sparql_extra_fields = '&type_response_query=csv';
    return sparql_extra_fields;
}

function get_sparql_string() {
    var sparql_string = editors[currentTabId].getValue();
    var unicode_string = toUnicode(sparql_string);
    return unicode_string;
}

// Convert string to Unicode
function toUnicode(theString) {
    var unicodeString = '';
    var regex = new RegExp(/[^\w\s\n\t`~!@#$%^&*()_|+\-=?;:'",.<>\{\}\[\]\\\/]/g);
    for (var j = 0; j < theString.length; j++) {
        if (theString.charAt(j).match(regex)) {
            var theUnicode = theString.charCodeAt(j).toString(16).toUpperCase();
            while (theUnicode.length < 4) {
                theUnicode = '0' + theUnicode;
            }
            theUnicode = '\\u' + theUnicode;
            unicodeString += theUnicode;
        } else {
            unicodeString += theString.charAt(j);
        }
    }
    return unicodeString;
}

function queryHref() {
    var respuesta = window.location.origin;
    var steps = window.location.pathname.split("/");
    for (var i = 1; i < (steps.length - 1); i++) {
        respuesta += "/" + steps[i];
    }
    return respuesta;
}

// LLM query JS
const llm_form = document.getElementById("llm"),
      loader = document.querySelector("#loading");

function displayLoading() {
    loader.classList.add("display");
}

function hideLoading() {
    loader.classList.remove("display");
}

for (var pair of data.entries()) {
    console.log(pair[0]+ ': ' + pair[1]);
}


llm_form.onsubmit = async function (event) {
    event.preventDefault();
    displayLoading();

    let data = new FormData();
    data.append("question", document.getElementById("question").value)
    data.append("apikey", document.getElementById("apikey").value)
// Check if fetching of api works and is being sent to the backend
    for (var pair of data.entries()) {
    console.log(pair[0]+ ': ' + pair[1]);
}

    let query = await fetch("llm", {method: "POST", body: data})
        .then(res => { hideLoading(); return res.text(); })
        .catch(err => console.error(err));

    tab = yasgui.getTab();
    tab.setName("LLM Query");
    tab.setQuery(query);
    tab.query();
};

const question_elem = document.getElementById("question"),
      submit_btn = document.getElementById("llm_submit"),
      questions = document.querySelectorAll('.question');

function handleClick(question) {
    question_elem.value = question;
    submit_btn.click();
}

questions.forEach(function(element) {
   element.addEventListener('click', function() {
       handleClick(element.textContent || element.innerText);
   });
});