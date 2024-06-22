'use strict';

$(function() {

    // Add author badge
     
    $("body").append(authorBadge);

    // Password visibility toggle
    $("input[type='password'][data-eye]").each(function(index) {
        var $passwordInput = $(this),
            toggleId = 'eye-password-' + index;

        $passwordInput.wrap($('<div/>', {
            style: 'position:relative',
            id: toggleId
        }));

        $passwordInput.css({
            paddingRight: 60
        });

        $passwordInput.after($('<div/>', {
            html: 'Show',
            class: 'btn btn-primary btn-sm',
            id: 'passeye-toggle-' + index
        }).css({
            position: 'absolute',
            right: 10,
            top: ($passwordInput.outerHeight() / 2) - 12,
            padding: '2px 7px',
            fontSize: 12,
            cursor: 'pointer'
        }));

        $passwordInput.after($('<input/>', {
            type: 'hidden',
            id: 'passeye-' + index
        }));

        var $invalidFeedback = $passwordInput.parent().parent().find('.invalid-feedback');

        if ($invalidFeedback.length) {
            $passwordInput.after($invalidFeedback.clone());
        }

        $passwordInput.on('keyup paste', function() {
            $('#passeye-' + index).val($(this).val());
        });

        $('#passeye-toggle-' + index).on('click', function() {
            if ($passwordInput.hasClass('show')) {
                $passwordInput.attr('type', 'password');
                $passwordInput.removeClass('show');
                $(this).removeClass('btn-outline-primary').text('Show');
            } else {
                $passwordInput.attr('type', 'text');
                $passwordInput.val($('#passeye-' + index).val());
                $passwordInput.addClass('show');
                $(this).addClass('btn-outline-primary').text('Hide');
            }
        });
    });

    // Form validation handling
    $('.my-login-validation').submit(function(event) {
        var form = $(this);
        if (form[0].checkValidity() === false) {
            event.preventDefault();
            event.stopPropagation();
        }
        form.addClass('was-validated');
    });

});
