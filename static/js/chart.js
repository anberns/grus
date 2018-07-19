var margin = {
    top: 10,
    right: 15,
    bottom: 10,
    left: 15
};

var width = 425 - margin.left - margin.right;
var height = 625 - margin.top - margin.bottom;


// /Create the svg where the visualization will reside
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
    .force("collide", d3.forceCollide(d => d.title ? 20 : 0))
    .on("tick", ticked);

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

var num_nodes;

/**
 * Reformat data from the server to fit the format of the visualization
 *
 * @param {*} json_data Json data from the server
 */
function parse_data(json_data) {
    // var data_obj = JSON.parse(json_data),
    //     visited_sites = Object.keys(data_obj).map(key => data_obj[key]),
    var visited_sites = Object.keys(json_data).map(key => json_data[key]),
        path = [];

    // Set the number of colored nodes we will have
    num_nodes = visited_sites.length;

    // Create the set of links for the visualization to use
    visited_sites.forEach(site => {
        // Add a link for a site we visited
        if (site.parent) {
            path.push({
                source: site.parent,
                target: site.url,
                in_path: true
            });
        }

        // Add links to ones found on pages
        site.links.forEach(href => {
            if (visited_sites.findIndex(el => el.url == href) == -1) {
                // Add a new site to our list of sites
                visited_sites.push({
                    url: href,
                    title: ""
                });
            }
            path.push({
                source: site.url,
                target: href,
                in_path: false
            });
        });
    });

    update({
        nodes: visited_sites,
        links: path
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
        .attr("stroke", d => d.in_path ? "#333" : "#666");

    // Delete removed links
    link.exit().remove();

    // Add any new links
    link = link.enter().append("line")
        .attr("stroke", d => d.in_path ? "#333" : "#666")
        .attr("stroke-width", d => d.in_path ? 2 : 1)
        .merge(link);


    // Update nodes
    node = node.data(data.nodes, d => d.url)
        .attr("r", d => d.title ? 5 : 3)
        .attr("fill", (d, i) => color(d, i));

    // Delete removed sites
    node.exit().remove();

    // Add any new sites
    node = node.enter().append("circle")
        .attr("fill", (d, i) => color(d, i))
        .attr("r", d => d.title ? 5 : 3)
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
        .text(d => d.title);

    // Delete removed sites
    title.exit().remove();

    // Add any new sites
    title = title.enter().append("text")
        .text(d => d.title)
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

function color(d, i) {
    var h = 0,
        s = 0,
        l = 55;
    if (d.title) {
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

// Test bfs data
var bfs_data = {
    a: {
        parent: null,
        url: "test.com",
        depth: 0,
        title: "Test",
        links: [
            "test.com/page1"
        ]
    },
    b: {
        parent: "test.com",
        url: "test.com/page1",
        depth: 1,
        title: "Page 1",
        links: [
            "test.com/page2",
            "test.com/page3",
        ]
    },
    c: {
        parent: "test.com/page1",
        url: "test.com/page2",
        depth: 2,
        title: "Page 2",
        links: [
            "test.com/page4",
            "test.com/page5",
        ]
    },
    d: {
        parent: "test.com/page1",
        url: "test.com/page3",
        depth: 2,
        title: "Page 3",
        links: [
            "test.com/page6",
            "test.com/page7",
        ]
    }
};

// Test dfs data
var dfs_data = {
    a: {
        parent: null,
        url: "test.com",
        depth: 0,
        title: "Test",
        links: [
            "test.com/page1"
        ]
    },
    b: {
        parent: "test.com",
        url: "test.com/page1",
        depth: 1,
        title: "Page 1",
        links: [
            "test.com/page2",
            "test.com/page3",
        ]
    },
    c: {
        parent: "test.com/page1",
        url: "test.com/page2",
        depth: 2,
        title: "Page 2",
        links: [
            "test.com/page4",
            "test.com/page5",
        ]
    },
    d: {
        parent: "test.com/page2",
        url: "test.com/page4",
        depth: 3,
        title: "Page 4",
        links: [
            "test.com/page6",
            "test.com/page7",
        ]
    }
};

parse_data(dfs_data);
setTimeout(() => parse_data(bfs_data), 2000);