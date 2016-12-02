(function(){

    var connector = tableau.makeConnector();

    var folder,
        template;

    var dataTypes = {
        'string': tableau.dataTypeEnum.string,
        'enum': tableau.dataTypeEnum.string,
        'float': tableau.dataTypeEnum.float,
        'date': tableau.dataTypeEnum.date
    };

    var me = this;
    me.vectors = [];
    me.columns = [];

    connector.getSchema = function(schemaCallback) {
        tableau.log("wdc schema connect ok");

        $.when(getColumns()).then(function(resp) {
            //resp = resp.length && resp[0];
            var cols = JSON.parse(resp).data;

            cols.map(function(item) {
                item.dataType = dataTypes[item.type];
                return item;
            });

            var tableInfo = {
                id : "box",
                alias : "box metadata info of the test folder",
                columns : cols
            };

            schemaCallback([tableInfo]);
         }, failure);
    };

    connector.getData = function(table, doneCallback) {

        $.when(getVectors()).then(function(resp) {
            //resp = resp.length && resp[0];
            var vectors = JSON.parse(resp).data;
            table.appendRows(vectors);
            doneCallback();
        }, failure);

    };

    function getVectors() {
        return $.ajax({
            url: "/api/vectors/" + template + "/" + folder,
            method: "GET"
        });
    }

    function getColumns() {
        return $.ajax({
            url: "/api/schema/" + template + "/" + folder,
            method: "GET"
        });
    }

    function failure(error) {
        alert(error);
    };

    $(document).ready(function() {
        folder = "none"; //$(".list-group-item.active").attr("value");
        template = "none"; //$(".template-list-item.active").attr("value");

        tableau.username = JSON.stringify({folder: folder, template: template});

        $(".list-group-item").click(function (e) {
            var self = this;
            e.preventDefault();

            var items = $("#folder-list").children();
            items.map(function() {
                this.classList.remove("active");
            });

            self.classList.add("active");
            folder = $(self).attr('value');

            $.ajax({
                url: '/api/set_folder/'+ folder,
                method: 'GET'
            });
        });

        $(".template-list-item").click(function(e) {
            var self = this;
            e.preventDefault();

            var items = $("#template-list").children();
            items.map(function() {
                this.classList.remove("active");
            });

            self.classList.add("active");
            template = $(self).attr("value");

            $.ajax({
                url: '/api/set_template/' + template,
                method: 'GET'
            });
        });

        $("#submitButton").click(function () {
            tableau.connectionName = "Box metadata test info";
            tableau.submit();
        });

        $("#logoutButton").click(function() {
            $.ajax({
                url: "/api/logout",
                method: "GET"
            }).done(function() {
                window.location.replace("/");
            });
        });

        $("#processButton").click(function() {
            $.ajax({
                url: '/api/process/' + template + "/" + folder,
                method: "GET"
            }).done(function(r) {
                alert(r);
            });
        });

        $("#downloadButton").click(function() {
            $.ajax({
                url: '/api/export/' + template + '/' + folder,
                method: "GET",
                complete: function(r) {
                    var data = r && r.responseText && JSON.parse(r.responseText);
                    window.location = data.data;
                }
            });
        });

        $("#uploadButton").click(function() {
            var formData = new FormData($("#importForm")[0]);
            var file = $("#importFile")[0].files[0];
            formData.append('file', file);
            $.ajax({
                url: '/api/import/' + folder,
                method: "POST",
                data: formData,
                cache: false,
                processData: false,
                dataType: 'json',
                contentType: false,
                success: function(response, textStatus, jqXHR) {
                    console.log(response);
                },
                error: function(err) {console.log(err);}
            });

            console.log(formData);
        });
    });


    tableau.registerConnector(connector);

})();
