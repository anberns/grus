var margin = {
    top: 10,
    right: 15,
    bottom: 10,
    left: 15
};

var width = 425 - margin.left - margin.right;
var height = 625 - margin.top - margin.bottom;
var num_nodes;
var old_nodes;


// Create the svg where the visualization will reside
var svg = d3.select('#chart')
    .append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)
    .call(responsivefy)
    .append('g')
    .attr('transform', `translate(${margin.left}, ${margin.top})`);

// Create the force simulation that governs the forces on the nodes
var simulation = d3.forceSimulation()
    .force("link", d3.forceLink().id(d => d.url))
    .force("charge", d3.forceManyBody())
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide(d => d.visited ? 20 : 0))
    .on("tick", ticked);

// Create arrows to show directionality
svg.append("svg:defs").selectAll("marker")
    .data(["in_path", "out_of_path"])
    .enter().append("svg:marker")
    .attr("id", String)
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 15)
    .attr("refY", 0)
    .attr("markerWidth", d => d == "in_path" ? 4 : 0)
    .attr("markerHeight", d => d == "in_path" ? 4 : 0)
    .attr('fill', "#333")
    .attr("orient", "auto")
    .append("svg:path")
    .attr("d", "M0,-5L10,0L0,5");

// A selection of all of the visual representations of the links
var link = svg.append("g")
    .attr("class", "links")
    .selectAll("line");

// A selection of all of the visual representations of the sites
var node = svg.append("g")
    .attr("class", "nodes")
    .selectAll("circle");

// A selection of all of the visual representations of the site names
var title = svg.append("g")
    .attr("class", "titles")
    .selectAll("text");


/**
 * Reformat data from the server to fit the format of the visualization
 *
 * @param {*} json_data Json data from the server
 */
function parse_data(json_data) {
    // var data_obj = JSON.parse(json_data),
    //     sites = Object.keys(data_obj).map(key => data_obj[key]),
    var sites = Object.keys(json_data).map(key => json_data[key]),
        links = [];

    // Set the number of colored sites we will have
    num_nodes = sites.length;

    // Create the set of links for the visualization to use
    sites.forEach(site => {
        // Because forEach works with a copy of the original, site can only be
        // a site we have visited. Mark it as such
        site.visited = true;

        // Add a link for a site we visited
        if (site.parent) {
            links.push({
                source: site.parent,
                target: site.url,
                in_path: true
            });
        }

        // Add links to ones found on pages
        site.links.forEach(href => {
            if (sites.findIndex(el => el.url == href) == -1) {
                // Add a new site to our list of sites
                sites.push({ url: href });
            }
            links.push({
                source: site.url,
                target: href,
                in_path: false
            });
        });
    });

    // Get the current nodes in the visualization to preserve positions
    var old_nodes = d3.selectAll('circle').data();
    sites.forEach(site => {
        var old_site = old_nodes.find(el => el.url == site.url);
        if (old_site) {
            site.x = old_site.x;
            site.y = old_site.y;
            site.vx = old_site.vx;
            site.vy = old_site.vy;
        }
    });

    update({
        nodes: sites,
        links: links
    });
}
/**
 * Sets the data used for the visualization
 *
 * @param {*} data Object containing the nodes and links to use for the viz
 */
function update(data) {

    // Update links
    link = link.data(data.links, d => d.source.url + "-" + d.target.url)
        .attr("stroke-width", d => d.in_path ? 2 : 1)
        .attr("stroke", d => d.in_path ? "#333" : "#666")
        .attr('marker-end', d => d.in_path ? 'url(#in_path)' : 'url(#out_of_path)');

    // Delete removed links
    link.exit().remove();

    // Add any new links
    link = link.enter().append("line")
        .attr("stroke", d => d.in_path ? "#333" : "#666")
        .attr("stroke-width", d => d.in_path ? 2 : 1)
        .attr('marker-end', d => d.in_path ? 'url(#in_path)' : 'url(#out_of_path)')
        .merge(link);


    // Update nodes
    node = node.data(data.nodes, d => d.url)
        .attr("r", d => d.visited ? 5 : 3)
        .attr("fill", (d, i) => color(d.visited, i));

    // Delete removed sites
    node.exit().remove();

    // Add any new sites
    node = node.enter().append("circle")
        .attr("fill", (d, i) => color(d.visited, i))
        .attr("r", d => d.visited ? 5 : 3)
        .call(d3.drag()
            .on("start", drag_started)
            .on("drag", dragged)
            .on("end", drag_ended))
        .merge(node);

    // Show URL on hover
    node.append("title")
        .text(d => d.url);

    // Update titles
    title = title.data(data.nodes, d => d.url)
        .text(d => d.title || "");

    // Delete removed sites
    title.exit().remove();

    // Add any new sites
    title = title.enter().append("text")
        .text(d => d.title || "")
        .call(d3.drag()
            .on("start", drag_started)
            .on("drag", dragged)
            .on("end", drag_ended))
        .merge(title);

    // Show URL on hover
    title.append("title")
        .text(d => d.url);

    // Set the nodes and links for the visualization
    simulation.nodes(data.nodes);
    simulation.force("link").links(data.links);
}

function color(was_visited, i) {
    var h = 0,
        s = 0,
        l = 55;
    if (was_visited) {
        h = (360 / (num_nodes) * i);
        s = 55;
    }
    return "hsl(" + h + ", " + s + "%, " + l + "%)";
}

function ticked() {
    link.attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

    node.attr("cx", d => d.x)
        .attr("cy", d => d.y);

    title.attr("x", d => d.x)
        .attr("y", d => d.y);
}

function drag_started(d) {
    if (!d3.event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
}

function drag_ended(d) {
    if (!d3.event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

function responsivefy(svg) {
    var container = d3.select(svg.node().parentNode),
        width = parseInt(svg.style("width")),
        height = parseInt(svg.style("height"));

    svg.attr("viewBox", "0 0 " + width + " " + height)
        .call(resize);

    d3.select(window).on("resize." + container.attr("id"), resize);

    function resize() {
        var target_width = parseInt(container.style("width"));
        var target_height = parseInt(container.style("height"));
        svg.attr("width", target_width);
        svg.attr("height", target_height);
    }
}

// // Test bfs data
// var bfs_data = {
//     a: {
//         parent: null,
//         url: "test.com",
//         depth: 0,
//         title: "Test",
//         links: [
//             "test.com/page1"
//         ]
//     },
//     b: {
//         parent: "test.com",
//         url: "test.com/page1",
//         depth: 1,
//         title: "Page 1",
//         links: [
//             "test.com/page2",
//             "test.com/page3",
//         ]
//     },
//     c: {
//         parent: "test.com/page1",
//         url: "test.com/page2",
//         depth: 2,
//         title: "Page 2",
//         links: [
//             "test.com/page4",
//             "test.com/page5",
//         ]
//     },
//     d: {
//         parent: "test.com/page1",
//         url: "test.com/page3",
//         depth: 2,
//         title: "Page 3",
//         links: [
//             "test.com/page6",
//             "test.com/page7",
//         ]
//     }
// };

// Test dfs data
// var dfs_data = {
//     a: {
//         parent: null,
//         url: "test.com",
//         depth: 0,
//         title: "Test",
//         links: [
//             "test.com/page1"
//         ]
//     },
//     b: {
//         parent: "test.com",
//         url: "test.com/page1",
//         depth: 1,
//         title: "Page 1",
//         links: [
//             "test.com/page2",
//             "test.com/page3",
//         ]
//     },
//     c: {
//         parent: "test.com/page1",
//         url: "test.com/page2",
//         depth: 2,
//         title: "Page 2",
//         links: [
//             "test.com/page4",
//             "test.com/page5",
//         ]
//     },
//     d: {
//         parent: "test.com/page2",
//         url: "test.com/page4",
//         depth: 3,
//         title: "Page 4",
//         links: [
//             "test.com/page6",
//             "test.com/page7",
//         ]
//     }
// };

// parse_data(dfs_data);
// setTimeout(() => parse_data(bfs_data), 2000);