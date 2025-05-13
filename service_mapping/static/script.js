// Field options for different entity types
let fieldOptions = {
    contact: {
        source: [], // Will be dynamically populated
        target: [
            { value: "hubspot_id", label: "HubSpot ID" },
            { value: "properties.firstname", label: "First Name" },
            { value: "properties.lastname", label: "Last Name" },
            { value: "properties.email", label: "Email" },
            { value: "properties.phone", label: "Phone" },
            { value: "properties.company", label: "Company" },
            { value: "properties.created_date", label: "Created Date" },
            { value: "properties.last_modified_date", label: "Last Modified Date" },
            { value: "properties.jobtitle", label: "Job Title" },
            { value: "properties.address", label: "Address" },
            { value: "properties.city", label: "City" },
            { value: "properties.state", label: "State" },
            { value: "properties.zip", label: "Zip Code" },
            { value: "properties.country", label: "Country" },
            { value: "properties.leadsource", label: "Lead Source" },
            { value: "properties.firstname1", label: "First Name (Custom)" },
            { value: "properties.lastname1", label: "Last Name (Custom)" }
        ]
    },
    deal: {
        source: [], // Will be dynamically populated
        target: [
            { value: "hubspot_id", label: "HubSpot Deal ID" },
            { value: "properties.dealname", label: "Deal Name" },
            { value: "properties.amount", label: "Amount" },
            { value: "properties.dealstage", label: "Deal Stage" },
            { value: "properties.closedate", label: "Close Date" },
            { value: "properties.hubspot_owner_id", label: "Owner ID" },
            { value: "associations.contactIds", label: "Contact IDs" },
            { value: "associations.companyIds", label: "Company IDs" },
            { value: "properties.createdate", label: "Created Date" },
            { value: "properties.hs_lastmodifieddate", label: "Last Modified Date" }
        ]
    },
    company: {
        source: [], // Will be dynamically populated  
        target: [
            { value: "hubspot_id", label: "HubSpot Company ID" },
            { value: "properties.name", label: "Company Name" },
            { value: "properties.domain", label: "Website Domain" },
            { value: "properties.description", label: "Description" },
            { value: "properties.industry", label: "Industry" },
            { value: "properties.phone", label: "Phone Number" },
            { value: "properties.address", label: "Address" },
            { value: "properties.city", label: "City" },
            { value: "properties.state", label: "State" },
            { value: "properties.zip", label: "Zip Code" },
            { value: "properties.country", label: "Country" },
            { value: "properties.createdate", label: "Created Date" },
            { value: "properties.hs_lastmodifieddate", label: "Last Modified Date" }
        ]
    }
};

// Function to add a new mapping rule
function addRule(sourceValue = '', targetValue = '') {
    const rulesDiv = document.getElementById('mapping-rules');
    const ruleDiv = document.createElement('div');
    ruleDiv.className = 'mapping-rule';
    
    // Get the current entity type
    const entityType = document.getElementById('entity-type').value;
    
    // Get the appropriate field options
    const sourceOptions = fieldOptions[entityType]?.source || [];
    const targetOptions = fieldOptions[entityType]?.target || [];
    
    // Create dropdown options HTML
    let sourceOptionsHtml = '<option value="">Select a field...</option>';
    sourceOptions.forEach(option => {
        const selected = option.value === sourceValue ? 'selected' : '';
        sourceOptionsHtml += `<option value="${option.value}" ${selected}>${option.label}</option>`;
    });
    
    let targetOptionsHtml = '<option value="">Select a field...</option>';
    targetOptions.forEach(option => {
        const selected = option.value === targetValue ? 'selected' : '';
        targetOptionsHtml += `<option value="${option.value}" ${selected}>${option.label}</option>`;
    });
    
    // Create the rule HTML
    ruleDiv.innerHTML = `
        <div style="flex: 1;">
            <label>From Oggo Field:</label>
            <select class="form-select source-field">
                ${sourceOptionsHtml}
            </select>
            <div class="helper-text">What it's called in your system</div>
        </div>
        
        <div class="big-arrow">→</div>
        
        <div style="flex: 1;">
            <label>To HubSpot Field:</label>
            <select class="form-select target-field">
                ${targetOptionsHtml}
            </select>
            <div class="helper-text">What it should become in HubSpot</div>
        </div>
        
        <button class="remove-btn" onclick="removeRule(this)">✕</button>
    `;
    
    rulesDiv.appendChild(ruleDiv);
}

// Function to remove a mapping rule
function removeRule(button) {
    if (confirm('Are you sure you want to remove this mapping?')) {
        button.parentElement.remove();
    }
}

// Function to load entity types dynamically
function loadEntityTypes() {
    fetch('/api/entity-types')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const entityTypeSelect = document.getElementById('entity-type');
            // Clear existing options
            entityTypeSelect.innerHTML = '';
            
            // Add new options
            if (data.entity_types && data.entity_types.length > 0) {
                data.entity_types.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type.value;
                    option.textContent = type.label;
                    entityTypeSelect.appendChild(option);
                });
                
                console.log(`Loaded ${data.entity_types.length} entity types`);
                
                // Load field options for the first entity type
                loadFieldOptions();
            } else {
                console.warn("No entity types found in the API response");
                // Add fallback options
                addFallbackEntityTypes();
            }
        })
        .catch(err => {
            console.error("Error loading entity types:", err);
            alert(`Could not load entity types: ${err.message}\nUsing default types instead.`);
            
            // Add fallback options and continue
            addFallbackEntityTypes();
            loadFieldOptions();
        });
}

// Function to add fallback entity types if API fails
function addFallbackEntityTypes() {
    const entityTypeSelect = document.getElementById('entity-type');
    entityTypeSelect.innerHTML = `
        <option value="contact">Contacts</option>
        <option value="project">Projects</option>
        <option value="contract">Contracts</option>
    `;
}

// Function to load source fields dynamically from the API
function loadFieldOptions() {
    const entityType = document.getElementById('entity-type').value;
    const loadingIndicator = document.getElementById('loading-fields');
    
    // Show loading indicator
    loadingIndicator.style.display = 'block';
    
    // Fetch source fields from our API
    fetch(`/api/source-fields/${entityType}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            loadingIndicator.style.display = 'none';
            
            if (data.fields && data.fields.length > 0) {
                // Replace the source fields with the dynamic ones
                fieldOptions[entityType].source = data.fields;
                console.log(`Loaded ${data.fields.length} source fields for ${entityType}`);
            } else {
                console.warn("No fields found in the API response");
                // Use fallback fields if no fields were returned
                setFallbackSourceFields(entityType);
            }
            // After updating fields, load the mapping
            loadMapping();
        })
        .catch(err => {
            loadingIndicator.style.display = 'none';
            console.error("Error loading source fields:", err);
            alert(`Could not load fields from Oggo: ${err.message}\nUsing default fields instead.`);
            
            // Set fallback fields and continue
            setFallbackSourceFields(entityType);
            loadMapping();
        });
}

// Function to set fallback source fields if API fails
function setFallbackSourceFields(entityType) {
    if (entityType === 'contact') {
        fieldOptions[entityType].source = [
            { value: "id", label: "ID" },
            { value: "first_name", label: "First Name" },
            { value: "last_name", label: "Last Name" },
            { value: "email", label: "Email Address" },
            { value: "phone", label: "Phone Number" },
            { value: "company", label: "Company Name" }
        ];
    } else if (entityType === 'deal') {
        fieldOptions[entityType].source = [
            { value: "id", label: "ID" },
            { value: "name", label: "Deal Name" },
            { value: "amount", label: "Amount" }
        ];
    } else if (entityType === 'company') {
        fieldOptions[entityType].source = [
            { value: "id", label: "ID" },
            { value: "name", label: "Company Name" }
        ];
    }
}

// Function to load existing mappings
function loadMapping() {
    const entityType = document.getElementById('entity-type').value;
    
    fetch(`/mappings/${entityType}`)
        .then(response => response.json())
        .then(data => {
            // Clear existing rules
            document.getElementById('mapping-rules').innerHTML = '';
            
            if (data.error) {
                // Add default mappings if none exist
                addDefaultMappings(entityType);
                return;
            }
            
            // Add rules from data
            const rules = data.rules || {};
            for (const [source, target] of Object.entries(rules)) {
                addRule(source, target);
            }
        })
        .catch(err => {
            console.error("Error loading mappings:", err);
            // Add default mappings on error
            addDefaultMappings(entityType);
        });
}

// Function to add default mappings based on entity type
function addDefaultMappings(entityType) {
    // Clear existing rules
    document.getElementById('mapping-rules').innerHTML = '';
    
    // Add default mappings based on entity type
    if (entityType === 'contact') {
        addRule('id', 'hubspot_id');
        addRule('first_name', 'properties.firstname1');
        addRule('last_name', 'properties.lastname1');
        addRule('email', 'properties.email');
        addRule('phone', 'properties.phone');
    } else if (entityType === 'deal') {
        addRule('id', 'hubspot_id');
        addRule('name', 'properties.dealname');
        addRule('amount', 'properties.amount');
    } else if (entityType === 'company') {
        addRule('id', 'hubspot_id');
        addRule('name', 'properties.name');
    }
}

// Function to save mappings
function saveMapping() {
    const entityType = document.getElementById('entity-type').value;
    const rules = {};
    let isValid = true;
    
    // Collect all rules and validate
    document.querySelectorAll('.mapping-rule').forEach(rule => {
        const sourceField = rule.querySelector('.source-field').value;
        const targetField = rule.querySelector('.target-field').value;
        
        if (!sourceField || !targetField) {
            alert('Please select both fields for each mapping!');
            isValid = false;
            return;
        }
        
        rules[sourceField] = targetField;
    });
    
    if (!isValid) return;
    
    // Save the mapping
    fetch(`/mappings/${entityType}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(rules)
    })
    .then(response => response.json())
    .then(data => {
        alert('✅ Settings saved successfully!');
    })
    .catch(err => {
        console.error("Error saving mappings:", err);
        alert('Error saving: ' + err);
    });
}

// Function to export mappings
function exportMapping() {
    const entityType = document.getElementById('entity-type').value;
    
    // Collect the current rules
    const rules = {};
    document.querySelectorAll('.mapping-rule').forEach(rule => {
        const sourceField = rule.querySelector('.source-field').value;
        const targetField = rule.querySelector('.target-field').value;
        
        if (sourceField && targetField) {
            rules[sourceField] = targetField;
        }
    });
    
    // Create a JSON file and trigger download
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(rules, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", `${entityType}_mapping.json`);
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
}

// Function to test mapping with sample data
function testMapping() {
    const entityType = document.getElementById('entity-type').value;
    const rules = {};
    
    // Collect all rules
    document.querySelectorAll('.mapping-rule').forEach(rule => {
        const sourceField = rule.querySelector('.source-field').value;
        const targetField = rule.querySelector('.target-field').value;
        
        if (sourceField && targetField) {
            rules[sourceField] = targetField;
        }
    });
    
    // Send to API for testing
    fetch(`/test-mapping/${entityType}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(rules)
    })
    .then(response => response.json())
    .then(data => {
        const resultsDiv = document.getElementById('test-results');
        resultsDiv.style.display = 'block';
        
        if (data.sample_output) {
            resultsDiv.innerHTML = `
                <div class="alert alert-success">
                    <h4>Sample Output:</h4>
                    <pre style="background: #f8f9fa; padding: 10px; border-radius: 5px;">${JSON.stringify(data.sample_output, null, 2)}</pre>
                </div>
            `;
        } else if (data.error) {
            resultsDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        }
    })
    .catch(err => {
        console.error("Error testing mapping:", err);
        document.getElementById('test-results').innerHTML = `
            <div class="alert alert-danger">
                Error testing mapping: ${err.message}
            </div>
        `;
        document.getElementById('test-results').style.display = 'block';
    });
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Handle file upload for import
    document.getElementById('file-input').addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        // Read the file
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const rules = JSON.parse(e.target.result);
                
                // Clear existing rules
                document.getElementById('mapping-rules').innerHTML = '';
                
                // Add rules from imported file
                for (const [source, target] of Object.entries(rules)) {
                    addRule(source, target);
                }
                
                alert('✅ Settings imported successfully!');
            } catch (error) {
                console.error("Error parsing import file:", error);
                alert('Error importing: Invalid JSON file');
            }
        };
        reader.readAsText(file);
    });

    // Update when entity type changes
    document.getElementById('entity-type').addEventListener('change', function() {
        loadFieldOptions();
    });

    // Initialize page
    loadEntityTypes();
    loadFieldOptions();
});