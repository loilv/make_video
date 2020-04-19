$('#fileupload').fileupload({
    dataType: 'json',
    dropZone: $('#dropzone'),
    add: function (e, data) {
        var table= $('#fileTable');
        table.show();
        var tpl = $('<tr class="file">' +
                    '<td class="fname"></td>' +
                    '<td class="preview"><img src="" alt=""></td>' +
                    '<td class="fsize"></td>' +
                    '<td class="fact">' +
                    '<a href="#" class="button rmvBtn text-danger"><i class="icon-cancel-2"></i>x</a>' +
                    '</td></tr>');
        var reader = new FileReader();
        reader.onload = function(e) {
            tpl.find('.preview img').attr('src', e.target.result);
        };
        reader.readAsDataURL(data.files[0]);
        tpl.find('.fname').text(data.files[0].name);
        tpl.find('.fsize').text(data.files[0].size);
        data.context = tpl.appendTo('#fileList');

        $('#start').click(function () {
            //fix this?
            data.submit();
        });
        $('#cancel').click(function () {
            data.submit().abort();
            tpl.fadeOut(function(){
                tpl.remove();
            });
            table.hide();
        });

        tpl.find('.rmvBtn').click(function(){
            if(tpl.hasClass('file')){
                data.submit().abort();
            }
            tpl.fadeOut(function(){
                tpl.remove();
            });
        });
        tpl.find('.uplBtn').click(function(){
            if(tpl.hasClass('file')){
                data.submit();
            }
            $(this).replaceWith('<p>done</p>');
            tpl.find('.rmvBtn').hide();
        });
        //var jqXHR = data.submit();
        //return false;
    },
    done: function (e, data) {
        $('#result').val('Upload finished.');
    },
    error: function (jqXHR, textStatus, errorThrown) {
        if (errorThrown === 'abort') {
            $('#result').val('File Upload has been canceled.');
        }
    }
});

