(function(){

    var connector = tableau.makeConnector();

    var folder, template;

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

    function baseCallback(vResp, cResp) {

        vResp = vResp.length && vResp[0];
        cResp = cResp.length && cResp[0];

        me.vectors = vResp && JSON.parse(vResp).data;
        me.columns = cResp && JSON.parse(cResp).data;

    };

    function failure(error) {
        alert(error);
    };

    $(document).ready(function() {
        folder = $(".list-group-item.active").attr("value");
        template = $(".template-list-item.active").attr("value");

        $(".list-group-item").click(function (e) {
            var self = this;
            e.preventDefault();

            var items = $("#folder-list").children();
            items.map(function() {
                this.classList.remove("active");
            });

            self.classList.add("active");
            folder = $(self).attr('value');
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
        });

        $("#submitButton").click(function () {

            tableau.username = "123";
            tableau.password = "321";

            tableau.connectionName = "Box metadata test info";
            tableau.submit();
        });

        $("#logoutButton").click(function() {
        });
    });

    tableau.registerConnector(connector);

})();
