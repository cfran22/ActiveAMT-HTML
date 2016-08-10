
var app = angular.module('manageHITs', []);

app.controller('manageHITsController', function ($scope) {

    //Variable initialization

    //Initial values for the table sorting
    $scope.sortBy = 'id';
    $scope.sortReverse = false;

    //Scope variables that map to what columns of the table are visible
    $scope.id = true;
    $scope.type = true;
    $scope.question = true;
    $scope.answer = true;
    $scope.img_src= false;
    $scope.template = false;
    $scope.completed = false;

    //Filter
    $scope.filter = '$';
    //List of the items that are clicked
    $scope.clickedItems = ['$'];
    //Map of the filter attributes
    $scope.filterBy = {
      $:'', id:'', type:'', question:'', answer:'', template:'', img_src:'', completed:''
    };
    //Maps to the values of the filter dropdown items being clicked
    $scope.dd = {
        $:true, id:false, type:false, question:false, answer:false, template:false, img_src:false, completed:false
    };
    //Text on the filter dropdown button
    $scope.dd_label = 'Any';
    //Simple mapping of filter names to the names they should be presented as
    var filter_map = {
        $:'Any', id:'ID', type:'Type', question:'Question', answer:'Answer', template:'Template', img_src:'Image Source', completed:'Completed'
    };


    //Scope function definitions

    // Helper function to remove an item from the list of clicked attributes
    var del_item = function(item){

        var el_index = $scope.clickedItems.indexOf(item);

            if(el_index > -1){
                $scope.clickedItems.splice(el_index, 1);
            }

    };

    // Function to put on each ng-click of the items in the filter dropdown
    $scope.clickDDitem = function(item){

        //Toggle the clicked attribute
        $scope.dd[item] = !$scope.dd[item];

        //If the attribute is toggled on...
        if($scope.dd[item]){

            //If the attribute happened to be all, un-click everything, wipe out all filter values.
            if(item == '$'){

                $scope.filterBy['$'] = $scope.filterBy[$scope.clickedItems[0]];

                var i = 0;

                while(i < $scope.clickedItems.length){

                    $scope.dd[$scope.clickedItems[i]] = false;
                    $scope.filterBy[$scope.clickedItems[i]] = "";

                    i++;
                }

                $scope.clickedItems.length = 0;
            }
                //Anything but the all, un-click the all and remove from the list of clicked attributes.
            else{
                $scope.dd['$'] = false;
                $scope.filterBy[item] = $scope.filterBy[$scope.filter];
                $scope.filterBy['$'] = "";
                del_item('$');
            }
            //Add the newly clicked item to the list of clicked attributes
            $scope.filter = item;
            $scope.clickedItems.push(item);
        }
            //If the attribute is toggled off un-click it and remove it from the list of clicked attributes, clear its filter value
        else{
            del_item(item);
            if($scope.filter == item && $scope.clickedItems.length >= 1){
                $scope.filter = $scope.clickedItems[0]
            }
            else{
                $scope.filterBy['$'] = $scope.filterBy[item];
            }
            $scope.dd[item] = false;
            $scope.filterBy[item] = "";
        }

        //Update the dropdown button text
            //If multiple attributes are clicked, make the label the first attribute with a plus sign
        if($scope.clickedItems.length > 1){
            $scope.dd_label = filter_map[$scope.clickedItems[0]] + ' +';
        }
            //If only one attribute is clicked, just make it that attribute
        else if($scope.clickedItems.length == 1){
            $scope.dd_label = filter_map[$scope.clickedItems[0]];
        }
            //If nothing is clicked, click any
        else{
            $scope.filter = '$';
            $scope.dd['$'] = true;
            $scope.clickedItems.push('$');
            $scope.dd_label = filter_map['$'];
        }
    };

    //Function to keep all filters in sync with the search text.
    //Should be called with an ng-change on the search box!
    $scope.updateFilters = function(searchText){
        var i = 0;

        while(i < $scope.clickedItems.length){
            $scope.filterBy[$scope.clickedItems[i]] = searchText;
            i++;
        }
    };

    //Custom filter to OR all of the filters currently in use.
    $scope.orFilter = function(hit){

        var match = false;
        var temp_bool;
        var hit_keys  = ['id', 'type', 'question', 'answer', 'template', 'img_src', 'completed'];
        var i = 0;

        //Handle filter any case individually as a HIT does not have the key '$'
        if($scope.filter == '$'){

            //Go through 'any' possible hit key
            while(i < hit_keys.length){

                //Only check for a match if that attribute is visible
                if($scope[hit_keys[i]]) {
                    temp_bool = hit[hit_keys[i]].toUpperCase().indexOf($scope.filterBy[$scope.filter].toUpperCase()) > -1;
                    match = temp_bool || match;
                    if (match) break;
                }

                i++;
            }

        }else {

            //Go through each selected filter
            while (i < $scope.clickedItems.length) {

                //Get the value of the filter criteria on this row
                temp_bool = (hit[$scope.clickedItems[i]].toUpperCase().indexOf($scope.filterBy[$scope.filter].toUpperCase()) > -1);
                match = temp_bool || match;
                if(match) break;

                i++;
            }
        }

        return match;
    };

    $scope.downReady = false;

    $scope.downloadTable = function(){

        var request = new XMLHttpRequest();
        var method = "POST";
        var url = "/downloadTable";
        var async = true;
        var params = "hit_ids=";

        request.open(method, url, async);

        request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

        request.onreadystatechange =  function () {
            if(request.readyState == 4 && request.status == 200) {
                console.log("Download ready...");
                $scope.downReady = true;
                $scope.dl_link = request.responseText;
                $scope.$apply();

            }
        };

        var i = 0;

        while(i < $scope.filtered_hits.length){

            params += $scope.filtered_hits[i].id + ',';

            i++;
        }

        request.send(params)

    }
    
});
