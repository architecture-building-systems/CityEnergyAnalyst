const {
  Spin,
  Icon,
  Button,
  Row,
  Col,
  Select,
  Card,
  Affix,
  Modal,
  Result
} = antd;
const { useState, useEffect, useCallback, useMemo } = React;

const INITIAL_DASHBOARD = 0;
const defaultPlotStyle = { height: 350, margin: 5 };

const Dashboard = () => {
  const [dashboards, setDashboards] = useState([]);
  const [dashIndex, setDashIndex] = useState(INITIAL_DASHBOARD);

  const handleClick = useCallback(index => {
    setDashIndex(index);
  }, []);

  useEffect(() => {
    axios
      .get("http://localhost:5050/api/dashboard/")
      .then(response => setDashboards(response.data));
  }, []);

  if (!dashboards.length) return null;

  const { layout, plots } = dashboards[dashIndex];

  return (
    <div id="cea-dashboard-content" style={{ minHeight: "100%" }}>
      <div id="cea-dashboard-content-title" style={{ margin: 10 }}>
        <DashSelect setDashIndex={handleClick} dashboards={dashboards} />
      </div>
      <div id="cea-dashboard-layout">
        {layout === "row" ? (
          <RowLayout dashIndex={dashIndex} plots={plots} />
        ) : (
          <GridLayout dashIndex={dashIndex} plots={plots} />
        )}
      </div>
    </div>
  );
};

const DashSelect = ({ setDashIndex, dashboards }) => {
  const dashList = useMemo(
    () =>
      dashboards.map((dashboard, index) => (
        <option key={index} value={index}>
          {dashboard.name}
        </option>
      )),
    [dashboards]
  );

  return (
    <Affix offsetTop={30}>
      <Select
        defaultValue={INITIAL_DASHBOARD}
        style={{ width: 200 }}
        onChange={value => setDashIndex(value)}
      >
        {dashList}
      </Select>
    </Affix>
  );
};

const ModalAddPlot = ({ visible, setVisible }) => {
  const handleOk = e => {
    setVisible(false);
  };

  const handleCancel = e => {
    setVisible(false);
  };

  return (
    <Modal
      title="Add plot"
      visible={visible}
      onOk={handleOk}
      onCancel={handleCancel}
    >
      <p>Some contents...</p>
    </Modal>
  );
};

const RowLayout = ({ dashIndex, plots }) => {
  if (!plots.length) return <h1>No plots found</h1>;
  const [modalAdd, setModelAdd] = useState(false);

  return (
    <React.Fragment>
      <ModalAddPlot visible={modalAdd} setVisible={setModelAdd} />
      {plots.map((data, index) => (
        <Row key={`${dashIndex}-${index}-${data.scenario}`}>
          <Col>
            <Plot index={index} dashIndex={dashIndex} data={data} />
          </Col>
        </Row>
      ))}
      <Affix offsetBottom={100}>
        <Button type="primary" style={{ float: "right" }} onClick={setModelAdd}>
          + Add plot
        </Button>
      </Affix>
    </React.Fragment>
  );
};

const GridLayout = ({ dashIndex, plots }) => {
  if (!plots.length) return <h1>No plots found</h1>;

  return (
    <React.Fragment>
      <div className="row display-flex">
        {plots.map((data, index) => (
          <div
            className="col-lg-4 col-md-12 col-sm-12 col-xs-12 plot-widget"
            key={`${dashIndex}-${index}-${data.scenario}`}
          >
            <Plot index={index} dashIndex={dashIndex} data={data} />
          </div>
        ))}
      </div>
    </React.Fragment>
  );
};

const Plot = ({ index, dashIndex, data, style }) => {
  const [div, setDiv] = useState(null);
  const [error, setError] = useState(null);
  const [hasIntersected, setIntersected] = useState(false);

  const plotStyle = { ...defaultPlotStyle, ...style };

  // TODO: Maybe find a better solution
  const hash = `cea-react-${dashIndex}-${index}`;

  // Get plot div
  useEffect(() => {
    axios
      .get(`http://localhost:5050/plots/div/${dashIndex}/${index}`)
      .then(response => {
        setDiv(() => {
          let script = null;
          let content = HTMLReactParser(response.data, {
            replace: function(domNode) {
              if (domNode.type === "script" && domNode.children[0]) {
                script = domNode.children[0].data;
              }
            }
          });
          return { content, script };
        });
      })
      .catch(_error => {
        setError(_error.response);
      });

    // Clean up script nodes on unmount
    return () => {
      let script = document.querySelector(`script[data-id=script-${hash}]`);
      if (script) script.remove();
    };
  }, []);

  // Mount script node when div is mounted
  useEffect(() => {
    if (div) {
      var _script = document.createElement("script");
      _script.dataset.id = `script-${hash}`;
      document.body.appendChild(_script);
      _script.append(div.script);
    }
  }, [div]);

  return (
    <Card
      title={
        <div>
          <span style={{ fontWeight: "bold" }}>{data.title}</span>
          {data.scenario && (
            <React.Fragment>
              <span> - </span>
              <small>{data.scenario}</small>
            </React.Fragment>
          )}
        </div>
      }
      extra="Test"
      style={{ ...plotStyle, height: "" }}
      bodyStyle={{ height: plotStyle.height }}
      size="small"
    >
      {div ? (
        div.content
      ) : error ? (
        <ErrorPlot error={error} />
      ) : (
        <LoadingPlot plotStyle={plotStyle} />
      )}
    </Card>
  );
};

const LoadingPlot = ({ plotStyle }) => {
  return (
    <Spin
      indicator={<Icon type="loading" style={{ fontSize: 24 }} spin />}
      tip="Loading Plot..."
    >
      <div style={{ height: plotStyle.height }} />
    </Spin>
  );
};

const ErrorPlot = ({ error }) => {
  console.log(error.status);
  if (error.status === 404) return HTMLReactParser(error.data);
  if (error.status === 500)
    return (
      <Result
        status="error"
        icon="Something went wrong!"
        title={error.status}
        subTitle={error.statusText}
      >
        <pre style={{ height: 200, overflow: "auto" }}>{error.data}</pre>
      </Result>
    );
  return null;
};

const EmptyPlot = () => {
  return <div>EmptyPlot</div>;
};

ReactDOM.render(
  React.createElement(Dashboard),
  document.querySelector("#cea-dashboard")
);

// To enable resize of Plotly plots
window.addEventListener("resize", function() {
  console.log("resizing");
  $.each($(".plotly-graph-div.js-plotly-plot"), function() {
    Plotly.Plots.resize($(this).attr("id"));
  });
});

document.getElementById("menu_toggle").addEventListener("click", function() {
  console.log("resizing");
  $.each($(".plotly-graph-div.js-plotly-plot"), function() {
    Plotly.Plots.resize($(this).attr("id"));
  });
});
