  const defaultFont = "Lato, Helvetica Neue, Arial, Helvetica, sans-serif";
  const defaultColors = ["#144d58", "#ff8a4e", "#ED561B", "#DDDF00", "#24CBE5", "#64E572", "#FF9655", "#FFF263", "#6AF9C4"]

  Highcharts.setOptions({
    colors: defaultColors,
    fontFamily: defaultFont,
    chart: {
      backgroundColor: "#fcfcfc",
      animation: false,
    },
    legend: {
      backgroundColor: "#fff",
      borderColor: "#dee2e6",
      borderWidth: 1,
    },
    credits: {
      text: "Generated by Metabolism of Cities",
      href: null,
      position: {
        y: -3,
        align: "center",
      },
      style: {
        fontSize: "12px",
        cursor: "default",
      },
    },
  });

  function createStackedBar(data) {
    Highcharts.chart("stacked", {
      chart: {
        type: "bar",
      },
      title: {
        text: "Stacked bar chart"
      },
      xAxis: {
        categories: data.x_axis
      },
      yAxis: {
        min: 0,
        title: {
          text: "y-axis"
        },
        stackLabels: {
          enabled: true,
          style: {
            color: "#212529"
          }
        }
      },
      legend: {
        reversed: true,
      },
      tooltip: {
        headerFormat: "<b>{point.x}</b><br/>",
        pointFormat: "{series.name}: {point.y}<br/>Total: {point.stackTotal}"
      },
      plotOptions: {
        series: {
          stacking: "normal",
        }
      },
      series: data.series
    });
  }

  function createLine(data) {
    Highcharts.chart("line", {
      title: {
        text: "Line graph"
      },
      yAxis: {
        min: 0,
        title: {
          text: "y-axis"
        },
      },
      xAxis: {
        categories: data.x_axis
      },
      tooltip: {
        headerFormat: "<b>{point.x}</b><br/>",
        pointFormat: "{series.name}: {point.y}<br/>Total: {point.stackTotal}"
      },
      plotOptions: {
        series: {
          marker: {
            enabled: false,
            symbol: "circle",
          }
        }
      },
      series: data.series
    });
  };

  function createArea(data) {
    Highcharts.chart("area", {
      chart: {
        type: "area"
      },
      title: {
        text: "Area graph"
      },
      yAxis: {
        min: 0,
        title: {
          text: "y-axis"
        },
      },
      xAxis: {
        categories: data.x_axis
      },
      tooltip: {
        headerFormat: "<b>{point.x}</b><br/>",
        pointFormat: "{series.name}: {point.y}<br/>Total: {point.stackTotal}"
      },
      plotOptions: {
        area: {
          stacking: "normal",
          lineColor: "#fcfcfc",
          lineWidth: 1,
          marker: {
            enabled: false,
            lineWidth: 1,
            lineColor: "#fcfcfc",
            symbol: "circle",
          }
        },
      },
      series: data.series
    });
  };

  function createDrilldown(data) {
    Highcharts.chart("drilldown", {
      chart: {
        type: "bar",
      },
      title: {
        text: "Drilldown bar chart"
      },
      xAxis: {
        type: "category"
      },
      yAxis: {
        min: 0,
        title: {
          text: "y-axis"
        },
        stackLabels: {
          style: {
            color: "#212529"
          }
        }
      },
      legend: {
        enabled: false,
      },
      tooltip: {
        headerFormat: "<b>{point.name}</b>",
        pointFormat: "{point.y:.0f}"
      },
      plotOptions: {
        series: {
          borderWidth: 0,
          dataLabels: {
            enabled: true,
            format: "{point.y:.0f}"
          }
        }
      },
      series: [
        {
          name: "Months",
          data: data.top_level
        }
      ],
      drilldown: {
        series: data.series
      }
  });
};

// pie chart variables, global so we can use them later
let pieChart;
let pieData = [];
let piePeriods = [];
let pieCurrent = 0;
let pieLast = 0;

function createPie(data) {
  pieData = data.series;
  piePeriods = data.x_axis;

  pieChart = Highcharts.chart("pie", {
    chart: {
      plotBackgroundColor: null,
      plotBorderWidth: null,
      plotShadow: false,
      type: "pie"
    },
    title: {
      text: "Pie chart"
    },
    tooltip: {
      pointFormat: "<b>{point.y:.0f}</b>"
    },
    plotOptions: {
      pie: {
        dataLabels: {
          enabled: false
        },
        showInLegend: true
      }
    },
    series: [{}]
  });

  $(".switch-pie").click(function() {
    let period = $(this).attr("data-period");
    openPie(period);
  })

  pieLast = piePeriods.length - 1;
  openPie(pieCurrent)
};

function openPie(period) {
  let periodValues = []

  $(pieData).each(function() {
    periodValues.push({
      name: this.name,
      y: this.data[period],
    });
  });

  pieChart.series[0].setData(periodValues);

  // various functions to update the toggles
  // to start, show current period in toggle menu
  $(".current-pie").text(piePeriods[period])

  let prevPeriod = Number(period) - 1;
  let nextPeriod = Number(period) + 1;

  // use this to update the buttons, making sure to disable them when on first or last period
  if (period == 0) {
    $(".prev-pie").addClass("disabled");
  } else {
    $(".prev-pie").removeClass("disabled").attr("data-period", prevPeriod);
  }

  if (period == pieLast) {
    $(".next-pie").addClass("disabled");
  } else {
    $(".next-pie").removeClass("disabled").attr("data-period", nextPeriod);
  }
}

// some variables we'll need later
let dataDefault;
let dataDrill;

let dataDefaultLoaded = false;
let dataDrillLoaded = false;

let stackedLoaded = false;
let drilldownLoaded = false;
let lineLoaded = false;
let areaLoaded = false;
let pieLoaded = false;
let mapLoaded = false;

$(".item-visualisations .nav-link").click(function() {
  let nav = $(this);
  let tab = nav.data("tab");
  let viz = nav.data("viz");

  $(".item-visualisations .nav-link, .tab-content .tab-pane").removeClass("active");
  $(".tab-pane#" + tab).addClass("active");
  nav.addClass("active");

  if (nav.data("drilldown") == true) {
    if (dataDrillLoaded == false) {
      $.get("/data/library/33053/data/json/?drilldown=true", function(data) {
        dataDrill = data;
        dataDrillLoaded = true;
        $(".tab-pane[data-drilldown='true']").removeClass("loading");
        createViz(viz)
      });
    } else {
      createViz(viz)
    }
  } else {
    if (dataDefaultLoaded == false) {
      $.get("/data/library/33053/data/json/", function(data) {
        dataDefault = data;
        dataDefaultLoaded = true;
        $(".tab-pane[data-drilldown!='true']").removeClass("loading");
        createViz(viz)
      });
    } else {
      createViz(viz)
    }
  }
})

function createViz(viz) {
  if (viz == "stacked" && stackedLoaded == false) {
    createStackedBar(dataDefault);
    stackedLoaded = true
  } else if (viz == "drilldown" && drilldownLoaded == false) {
    createDrilldown(dataDrill)
    drilldownLoaded = true
  } else if (viz == "line" && lineLoaded == false) {
    createLine(dataDefault)
    lineLoaded = true
  } else if (viz == "area" && areaLoaded == false) {
    createArea(dataDefault)
    areaLoaded = true
  } else if (viz == "pie" && pieLoaded == false) {
    createPie(dataDefault)
    pieLoaded = true
  } else if (viz == "map" && mapLoaded == false) {
    createMap(dataDefault)
    mapLoaded = true
  }
}

// first visualisation to open
$(".nav-link[data-tab='stacked']").click();
