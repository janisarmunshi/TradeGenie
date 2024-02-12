function showToast(message, status = 200, type = '', msgTime = 0, wait = 4000) {
    // document.getElementById('appMsgBody').innerHTML = message;
    // $("#appMsg").toast({
    //     autohide: true,
    //     delay: wait,
    // });
    // $("#appMsg").toast('show');
    debugger;
    if (type==''){
        if (status == '200'){
            type = 'warning';
        }
        else if(status=='000'){
            type = 'light';
        }
        else {
            var type = 'error';
        }
    }
    let msgClass = 'text-bg-' + type;    
    document.getElementById('appMsgBody').innerHTML = message;
    if (parseInt(msgTime) > 0) {
        document.getElementById('appMsgMinutes').innerHTML = msgTime + ' minutes ago';
    }
    var toastLiveExample = document.getElementById('appMsg')    
    toastLiveExample.classList.add(msgClass)
    // toastLiveExample.className += ' ' + msgClass

    var toast = new bootstrap.Toast(toastLiveExample, { delay: wait });
    toast.show()
    // toastLiveExample.classList.remove(msgClass)
        // removeClass('appMsg', msgClass);
}

function ajaxCall(ipUrl, callType = "POST", dataIn) {
    if (callType=="POST" || callType=="post"){
        csrfToken = $('#txtcsrf').val()
        dataIn['csrfmiddlewaretoken'] = csrfToken
        $.ajaxSetup({
            beforeSend: function (xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrfToken);
                }
            }
        });
    
    }

    return $.ajax({
        type: callType,
        url: ipUrl,
        //dataType: "json", //I tried using this and commenting it out and it made no diff.
        //contentType: "application/json", //I tried using this and commenting it out and it made no diff.
        async: false,
        data: dataIn,
        success: function(response) {
            
            return response;
            
        },
        failure: function (errMsg) {
            console.log(errMsg);
        }
    });
    debugger;
    // return $.ajax({
    //     url: ipUrl,
    //     type: callType,
    //     beforeSend: function (xhr, settings) {
    //         xhr.setRequestHeader("X-CSRFToken", csrfToken);
    //     },        
    //     data: dataIn,
    //     async: false,
    //     dataType: "json",
    //     success: function(response) {
    //         // alert('success');
    //         return response;
    //     },
    //     error: function(err) {
    //         // alert("fail" + JSON.stringify(err));
    //         // return err;
    //     }, //error
    // });
    //alert('in js'+ retData);
    //return retData;     
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
  }

function ajaxCallChar(ipUrl, callType = "POST", dataIn) {

    return $.ajax({
        url: ipUrl,
        type: callType,
        data: dataIn,
        async: false,
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
            return response;
        },
        error: function (err) {

        }, //error
    });

}

function setClass(element, className) {
    eleItem = document.getElementById(element);
    eleItem.className = className;
}

function helpData(DataModel, Filters, urlData='/helpData', fields=[]){
    if (urlData == ''){
        urlData = '/helpData'
    }
    var tData = {  
        Model: DataModel,
        Fields: JSON.stringify(fields),
        Filters: JSON.stringify(Filters),        
    };
  
    let lstJSON = ajaxCall(urlData, 'GET', tData); 
    return lstJSON;
}
