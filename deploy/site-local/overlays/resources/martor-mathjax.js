jQuery(function ($) {
    $(document).on('martor:preview', function (e, $content) {
        function update_math() {
            MathJax.startup.promise.then(function () {
                return MathJax.typesetPromise([$content[0]]);
            }).then(function () {
                $content.find('.tex-image').hide();
                $content.find('.tex-text').show();
            });
        }

        var $jax = $content.find('.require-mathjax-support');
        if ($jax.length) {
            var mathjaxRoot = new URL('vendor/mathjax-3.2.2/es5',
                new URL($jax.attr('data-config'), window.location.href)).href;
            if (!('MathJax' in window)) {
                $.ajax({
                    type: 'GET',
                    url: $jax.attr('data-config'),
                    dataType: 'script',
                    cache: true,
                    success: function () {
                        window.MathJax.startup = {typeset: false};
                        window.MathJax.loader = {paths: {mathjax: mathjaxRoot}};
                        $.ajax({
                            type: 'GET',
                            url: mathjaxRoot + '/tex-chtml.js',
                            dataType: 'script',
                            cache: true,
                            success: update_math
                        });
                    }
                });
            } else {
                update_math();
            }
        }
    })
});
