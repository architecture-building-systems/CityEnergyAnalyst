const { Spin, Icon, Button, Row, Col } = antd;
const { useState, useEffect } = React;

function Dashboard() {
  const [dashIndex, setDashIndex] = useState(0);
  const [plots, setPlots] = useState([]);

  const handleChange = event => {
    setDashIndex(event.target.value);
  };

  const renderDash = () => {
    let _plots = [];
    let numOfplots = 3;
    for (var index = 0; index < numOfplots; index++) {
      _plots.push(index);
    }
    setPlots(_plots);
  };

  useEffect(() => {
    renderDash();
  }, [dashIndex]);

  useEffect(() => {
    console.log(plots);
  }, [plots]);

  return (
    <div>
      <input type="text" value={dashIndex} onChange={handleChange} />
      {plots.map(index => (
        <Plot key={index} id={index} dashIndex={dashIndex} />
      ))}
    </div>
  );
}

function Plot({ id, dashIndex }) {
  const [plotWidth, plotHeight] = [500, 500];
  const [div, setDiv] = useState(null);
  const [script, setScript] = useState(null);
  const [error, setError] = useState(null);

  // TODO: Get the hash
  const hash = `abced-${id}`;

  useEffect(() => {
    axios
      .get(`http://localhost:5050/plots/div/${dashIndex}/${id}`)
      .then(response => {
        setDiv(
          HTMLReactParser(response.data, {
            replace: function(domNode) {
              if (domNode.type === "script") {
                // setScript(domNode.children[0].data);
              }
            }
          })
        );
      })
      .catch(error => {
        setError(error);
      });
  }, []);

  useEffect(() => {
    if (script) {
      var _script = document.createElement("script");
      _script.dataset.id = hash;
      document.body.appendChild(_script);
      _script.append(script);
    }
    if (!script) {
      var _script = document.querySelector(`script[data-id=${hash}]`);
      if (_script) _script.remove();
    }
  }, [div]);

  return (
    <div>
      <Button
        onClick={() => {
          setError(null);
          setScript(null);
          setDiv(null);
        }}
      >
        Remove Plot
      </Button>
      <div style={{ height: plotHeight, width: plotWidth }}>
        <Spin
          spinning={!div && !error}
          indicator={<Icon type="loading" style={{ fontSize: 24 }} spin />}
        >
          {div || <div style={{ height: plotHeight, width: plotWidth }} />}
        </Spin>
      </div>
    </div>
  );
}

ReactDOM.render(
  React.createElement(Dashboard),
  document.querySelector("#cea-dashboard")
);
