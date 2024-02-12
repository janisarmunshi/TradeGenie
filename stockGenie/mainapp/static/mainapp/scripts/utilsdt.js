var listing;
$(document).ready(function () {

 
    // $('#listing tbody').on('click', 'tr', function () {
    //     if ($(this).hasClass('selected')) {
    //         $(this).removeClass('selected');
    //     } else {
    //         listing.$('tr.selected').removeClass('selected');
    //         $(this).addClass('selected');
    //     }
    // });
 
});

function generateColumnSource(colDef, firstCol = '', defaultField = true, addClass = true) {
    var colSource = [],
        sourceLen = colDef.length,
        colCount = 0;
        idVisible = false;
        
    // colCount1 = 6
    // if (checkbox) { colCount1 += 1; }

    // colCount2 = document.getElementById('help').rows[0].cells.length
    // if (checkbox == true) { sourceLen = sourceLen + 1; }
    // if (colCount1 > colCount2) { colCount = colCount1 } else { colCount = colCount2 }
    if (firstCol=='id') {
        idVisible = true;
    }
    if (firstCol=='check') {
        src = {
            data: 'id',
            // defaultContent: "",
            targets: 0,
            searchable: false,
            orderable: false,
            width: '1%',
            // className: 'dt-body-center',
            // className: 'select-checkbox',
            render: function(data, type, full, meta) {
                return '<input type="checkbox" >';
            }

        }        
    }else{
        src = {
            data: 'id',
            visible: idVisible,
            targets: 0,
            searchable: false,
            orderable: false,
            width: '1%',

        }                
    }
    colSource.push(src);

    colCount = 7;
    for (i = 0; i < sourceLen; i++) {
        // if (checkbox == true && i > 0) {
        //     src = {
        //         data: colDef[i - 1].column_Header,
        //     };
        //     if (colDef[i - 1].column_class != "") {
        //         src['className'] = colDef[i - 1].column_class
        //     }
        // } else {

        src = {
            data: colDef[i].columnHeader
        }
        if (addClass == true) {
            if (colDef[i].column_class != "") {
                src['className'] = colDef[i].columnclass
            }
        }

        // }
        // -------------------------------------
        colSource.push(src);
    }
    // if (firstCol!= '') { sourceLen += 1; }
    sourceLen += 1;
    if (defaultField == true) {
        for (i = sourceLen; i < colCount; i++) {
            src = {
                data: colDef[0].columnHeader,
                visible: false
            }
            colSource.push(src);
        }
    }

    return colSource;
}

function initializeListing(listElement, Model, filters = {},firstcol, column7=false, urlData='/helpData/', fields = []) {
    debugger;
        if (urlData == '') {
            urlData = '/helpData/'
        }
        let ElementName = listElement
        if (listElement.substr(0, 1) != "#") {
            ElementName = '#' + listElement;
        }
        var tData = { Model: Model, Filters: {} } //'Filters': ''
        var colHeading = ajaxCallChar('/helpHeader/', 'GET', tData);
        if (colHeading.status == 200) {
            var colDef = colHeading.responseJSON.data;
        }
    
    
        var colSource = generateColumnSource(colDef, firstcol, column7, false);
        debugger;
        listing = $(ElementName).DataTable({
            select: {
                style: 'single'
            },
            ajax: {
                url: urlData,
                // dataSrc: dataSrc,
                type: 'GET',          
                data: {
                    csrfmiddlewaretoken: $('#txtcsrf').val(),
                    Model: Model,                
                    Filters: JSON.stringify(filters),
                    Fields: JSON.stringify(fields)
                },
            },
            destroy: true,
            columns: colSource,
        });
        debugger;
        for (i = 0; i <= colDef.length; i++) {
            if (i == 0 ){
                if (firstcol=='check'){
                    listing.columns(i).header().to$().text('check');        
                }else{
                    listing.columns(i).header().to$().text('id');    
                }
            }else{
                listing.columns(i).header().to$().text(colDef[i - 1].columnLable);
            }
            // console.log(helpTable.column(i).dataSrc());
        }
        // for (i = colDef.length; i<8; i++) {
        //     listing.columns(i).header().to$().text(colDef[0].column_Lable);

        //     // console.log(helpTable.column(i).dataSrc());
        // }


        return listing;
    }
    