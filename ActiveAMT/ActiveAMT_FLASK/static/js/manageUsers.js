
var app = angular.module('manageUsers', []);

app.controller('manageUsersController', function($scope, $http, $window) {

    //Initialization of scope variables

    //Start by searching the table by any attribute
    $scope.filter = "$";
    //Start by labeling the filter dropdown menu with 'Any'
    $scope.dd_label = 'Any';
    //Initialize the dictionary of available filters
    $scope.filterBy = {
        $:'', id:'', password:'', is_admin:''
    };
    //Set the checked attributes in the dropdown list
    $scope.dd = {
      any:true, id:false, password:false, is_admin:false
    };


    //Scope function declarations

    //HTML callable function to change the currently used filter
    //Preserves the currently entered search text
    $scope.changeFilter = function(new_filt){
        $scope.filterBy[new_filt] = $scope.filterBy[$scope.filter];
        $scope.filterBy[$scope.filter] = "";
        $scope.filter = new_filt
    };


    //HTML callable function to POST a delete request for a user, by ID.
    $scope.delUser = function(userId) {

        var data = $.param({
            user : userId
        });

        var config = {
           headers : {
               'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8;'
           }
        };

        $http.post("/delUser", data, config);
        $window.location.reload();
    };


    //HTML callable function to POST a new user to the USER database
    $scope.addUser = function(){

        var data = $.param({
            username : $scope.username_in_add,
            password : $scope.password_in_add,
            is_admin : $scope.is_admin_in_add
        });

        var config = {
           headers : {
               'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8;'
           }
        };

        $http.post('/addUser', data, config)
            .then(function successCallback(response) {
                $window.location.reload();
                }, function errorCallback(response){
                $scope.addError = true;
                $scope.addErrorMessage = response.data
            });
    };


    //HTML callable function to POST updated attributes back to the USER database
    $scope.updateUser = function(user, edit){

        var data = $.param({
            old_username : user.id,
            username : edit.username || user.id,
            password : edit.password || user.password,
            is_admin : edit.admin
        });

        var config = {
           headers : {
               'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8;'
           }
        };

        $http.post('/updateUser', data, config)
            .then(function successCallback(response){
                $window.location.reload();
                $scope.data = response.data
            }, function errorCallback(response) {
                $scope.updateError = true;
                $scope.updateErrorMessage = response.data
            });
    };

});
