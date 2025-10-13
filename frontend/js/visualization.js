// d3.select() // Helps select elements in the DOM
//   .append() // Appends new elements to the DOM
//   .attr()   // Sets attributes for the selected elements
//   .style()  // Sets CSS styles for the selected elements
//     .data()   // Binds data to the selected elements

// d3.select("body").style("font-family", "Arial, sans-serif");
// d3.select("body").size = "100%";
// d3.select("body").append("p").text("Welcome to NYC Taxi Explorer!");
// d3.select("body").style("background-color", "#f9f0f0");
// d3.select("p").style("color", "blue").style("font-size", "20px");
// d3.select("p").align("center"); // Center align the text

// d3.select("body").append("h1").text("My Bar Graph Created using D3js").style("text-align", "left").style("text-align", "up").style("color", "#0942ffff");
// var dataset = [150, 20, 30, 140, 45, 60, 70, 80, 90, 120, 110, 130, 100, 40, 10];
// var dataset = [1, 2, 3, 4, 5]; // Example dataset to use for implementing scale.

// var svgWidth = 500, svgHeight = 300, barPadding = 5;
// var barWidth = svgWidth / dataset.length;

// var svg = d3.select('svg')
//     .attr("width", svgWidth)
//     .attr("height", svgHeight);

// var barChart = svg.selectAll("rect")
//     .data(dataset)
//     .enter()
//     .append("rect")
//     .attr("y", function (d) {
//         return svgHeight - d
//     })
//     .attr("height", function (d) {
//         return d;
//     })
//     .attr("fill", "#84aafcff")

//     .attr("width", barWidth - barPadding) // Set the width of each bar
//     .attr("transform", function (d, i) {
//         var translate = [barWidth * i, 0];
//         return "translate(" + translate + ")";
//     });

// var text = svg.selectAll("text")
//     .data(dataset)
//     .enter()
//     .append("text")
//     .text(function (d) {
//         return d;
//     })
//     .attr("y", function (d, i) {
//         return svgHeight - d - 2;
//     })
//     .attr("x", function (d, i) {
//         return barWidth * i + (barWidth - barPadding) / 2;
//     })
//     .attr("text-anchor", "middle")
//     .attr("fill", "#378cfcff");

// // Define the scales

// var yScale = d3.scaleLinear()
//     .domain([0, d3.max(dataset)]) // Input domain
//     .range([0, svgHeight]); // Output range (inverted for SVG coordinates)

// var barChart = svg.selectAll("rect") // Update the bars with the new scale
//     .data(dataset)
//     .enter() // Use enter() to create new bars for new data points
//     .append("rect")
//     .attr("y", function (d) {
//         return svgHeight - yScale(d); // Use the scaled value for height
//     })

// var dataset = [1, 2, 3, 4, 5]; // Example dataset to use for implementing scale.

// var svgWidth = 500, svgHeight = 300, barPadding = 10; // Padding between bars
// var barWidth = svgWidth / dataset.length; // Width of each bar based on dataset length

// var yScale = d3.scaleLinear() // Define the yScale
//     .domain([0, d3.max(dataset)]) // Input domain (data values)
//     .range([0, svgHeight]); // Maps data to pixel height

// var svg = d3.select('svg') // Select the SVG element
//     .attr("width", svgWidth) // Set SVG width
//     .attr("height", svgHeight); // Set SVG height

// svg.selectAll("rect") // Create bars for the bar chart
//     .data(dataset) // Bind data to rectangles
//     .enter() // Create new rectangles for new data points
//     .append("rect")// Append a rectangle for each data point
//     .attr("y", function (d) { // Set the y position of each bar
//         return svgHeight - yScale(d); // Position from bottom. yScale inverts the height
//     })
//     .attr("height", function (d) { // Set the height of each bar
//         return yScale(d); // Use the scaled value for height
//     })
//     .attr("width", barWidth - barPadding) // Set the width of each bar with padding
//     .attr("transform", function (d, i) { // Position each bar horizontally
//         var translate = [barWidth * i, 0]; // Calculate x position based on index
//         return "translate(" + translate + ")"; // Apply translation
//     })
//     .attr("fill", "#84aafcff"); // Set bar color

// svg.selectAll("text") // Add text labels to each bar
//     .data(dataset) // Bind data to text elements
//     .enter() // Create new text elements for new data points
//     .append("text") // Append a text element for each data point
//     .text(function (d) { // Set the text content
//         return d; // Display the data value
//     })
//     .attr("y", function (d) { // Set the y position of the text
//         return svgHeight - yScale(d) - 5; // Position above the bar with a small offset
//     })
//     .attr("x", function (d, i) { // Set the x position of the text
//         return barWidth * i + (barWidth - barPadding) / 2; // Center the text within the bar
//     })
//     .attr("text-anchor", "middle") // Center align the text
//     .attr("fill", "#378cfcff"); // Set text color

// Note: This code assumes there is an <svg> element in the HTML where the bar chart will be rendered.

// Additional enhancements like axes, tooltips, and interactivity can be added as needed.

// Lets add axes to the bar chart for better readability

// var data = [80, 100, 56, 120, 180,30, 40, 120, 160]

// var svgWidth = 600, svgHeight = 300;

// var svg = d3.select('svg')
//     .attr("width", svgWidth)
//     .attr("height", svgHeight);
//     // define svg background color.
//     svg.style("background-color", "#69afffff");


// var xScale = d3.scaleLinear()
//     .domain([0, d3.max(data)])
//     .range([0, svgWidth]);


// var yScale = d3.scaleLinear()
//     .domain([0, d3.max(data)])
//     .range([svgHeight, 0]);

// var x_axis = d3.axisBottom().scale(xScale);

// var y_axis = d3.axisLeft().scale(yScale);

// svg.append("g")
//     .attr("transform", "translate(50, 10)")
//     .call(y_axis);

// var xAxisTranslate = svgHeight - 20; // to translate our x axis

// svg.append("g")
//     .attr("transform", "translate(50, " + xAxisTranslate + ")")
//     .call(x_axis);

// LET'S CREATE A PAI CHART

var data = [
    { "platform": "Android", "percentage": 40.11 },
    { "platform": "Windows", "percentage": 36.69 },
    { "platform": "iOS", "percentage": 13.06 }
];

var svgWidth = 500, svgHeight = 300, radius = Math.min(svgWidth, svgHeight) / 2;
var svg = d3.select('svg')
    .attr("width", svgWidth)
    .attr("height", svgHeight);

// create a group element to hold pai chart

var g = svg.append("g")
    .attr("transform", "translate(" + radius + "," + radius + ")");

var color = d3.scaleOrdinal(d3.schemeCategory10); // 

var pie = d3.pie().value(function (d) {
    return d.percentage;
});

var path = d3.arc()
    .outerRadius(radius)
    .innerRadius(0);

var arc = g.selectAll("arc")
    .data(pie(data))
    .enter()
    .append("g"); // create group for each slice

arc.append("path")
    .attr("d", path)
    .attr("fill", function(d) { return color(d.data.percentage);});

var label = d3.arc()
.outerRadius(radius)
.innerRadius(0)