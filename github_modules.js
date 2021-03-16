const module_fields = ['display_name', 'name', 'summary', 'version']

function loadJSON(callback) {
    let file_url = "https://myrrkel.github.io/odoo_one/data/github_modules_12.json"
    //let file_url = "./data/github_modules_12.json" // for tests
    $.getJSON(file_url, function (result) {
        $.each(result, function (i, field) {
            if (i) {
                addUser(i, field);
            }
        });
    });
}

function addHeaders(table_id, keys) {
    $thead = $('#' + table_id + ' > thead > tr');
    $.each(module_fields, function (i, field) {
        $thead.append('<th>' + field + '</th>');
    })
}

function addUser(user_name, user) {
    $.each(user.repositories, function (repository_name, repository) {
        addRepository(user_name, repository);
    })
}

function addRepository(user_name, repository) {
    let i = 0;
    let table_id = user_name + '_' + repository.name;
    $("#container").append('<h2>' + user_name + ' - ' + repository.name + '</h2>')
    $("#container").append($('<table></table>').addClass("table").attr('id', user_name + '_' + repository.name));
    let table = $("#" + table_id);
    table.append($('<thead><tr></tr></thead>'));
    table.append($('<tbody></tbody>'));
    $.each(repository.modules, function (module_name, module) {
        if (i === 0) {
            addHeaders(table_id, Object.keys(module));
        }
        addModule(table_id, module);
        i++;
    })
}

function addModule(table_id, module) {
    let row = $('#' + table_id + ' > tbody').append($('<tr></tr>'));
    $.each(module_fields, function (i, key) {
        row.append('<td>' + module[key] + '</td>');
    })
}

function showTable(users) {
    $.each(users, function (user_name, user) {
        addUser(user_name, user);
    })
}


$().ready(function () {
    loadJSON();
});
