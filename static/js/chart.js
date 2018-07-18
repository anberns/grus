(function() {
    var margin = {
        top: 10,
        right: 15,
        bottom: 10,
        left: 15
    }
    var width = 425 - margin.left - margin.right;
    var height = 625 - margin.top - margin.bottom;

    var svg = d3.select('#chart')
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .style('background-color', 'lightblue')
        .call(responsivefy)
        .append('g')
        .attr('transform', `translate(${margin.left}, ${margin.top})`);



    function responsivefy(svg) {
        var container = d3.select(svg.node().parentNode),
            width = parseInt(svg.style("width")),
            height = parseInt(svg.style("height"));

        svg.attr("viewBox", "0 0 " + width + " " + height)
            .call(resize);

        d3.select(window).on("resize." + container.attr("id"), resize);

        function resize() {
            var targetWidth = parseInt(container.style("width"));
            var targetHeight = parseInt(container.style("height"));
            svg.attr("width", targetWidth);
            svg.attr("height", targetHeight);
        }
    }

})();