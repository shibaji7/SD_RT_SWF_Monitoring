
function searchTable() {
    var input, filter, table, tr, td, i, j, txtValue;
    input = document.getElementById("table_input");
    filter = input.value.toUpperCase();
    table = document.getElementById("flare_table");
    tr = table.getElementsByTagName("tr");

    // Loop through all table rows, and hide those that don't match the search query
    for (i = 1; i < tr.length; i++) { // Start from 1 to skip the header row
        tr[i].style.display = "none"; // Hide row by default
        td = tr[i].getElementsByTagName("td");
        for (j = 0; j < td.length; j++) {
            txtValue = td[j].textContent || td[j].innerText;
            if (txtValue.toUpperCase().indexOf(filter) > -1) {
                tr[i].style.display = ""; // Show row if match found
                break; // Break out of inner loop once a match is found in the row
            }
        }
    }
}

function createTable(){
    var tableBody = document.getElementById("flare_table_body");
    events.forEach(function(item) {
        // Create a table row
        var row = document.createElement("tr");
    
        // Create table cells for each data property
        for (var key in item) {
        if (item.hasOwnProperty(key)) {
            var cell = document.createElement("td");
            var text = document.createTextNode(item[key]);
            cell.appendChild(text);
            row.appendChild(cell);
        }
        }
    
        // Append the row to the table body
        tableBody.appendChild(row);
    });
}