import flask as f


from ..api import rule
from ..api._comparator import BenchmarkComparator, BenchmarkListComparator
from ..api._endpoint import ApiEndpoint
from ..entities._entity import NotFound
from ..entities.summary import Summary
from ..hacks import set_display_batch, set_display_name


def _compare_entity(summary):
    return {
        "id": summary.id,
        "batch_id": summary.batch_id,
        "run_id": summary.run_id,
        "value": summary.mean,
        "unit": summary.unit,
        "benchmark": summary.display_name,
        "batch": summary.display_batch,
    }


class CompareBenchmarksAPI(ApiEndpoint):
    def _get(self, benchmark_id):
        try:
            summary = Summary.one(id=benchmark_id)
        except NotFound:
            self.abort_404_not_found()
        return summary

    def get(self, compare_ids):
        """
        ---
        description: Compare benchmark results.
        responses:
            "200": "CompareEntity"
            "401": "401"
            "404": "404"
        parameters:
          - name: compare_ids
            in: path
            schema:
                type: string
            example: <baseline_id>...<contender_id>
          - in: query
            name: raw
            schema:
              type: boolean
          - in: query
            name: threshold
            schema:
              type: integer
        tags:
          - Compare
        """
        raw = f.request.args.get("raw", "false").lower() in ["true", "1"]
        threshold = f.request.args.get("threshold")
        if threshold is not None:
            threshold = int(threshold)

        try:
            baseline_id, contender_id = compare_ids.split("...", 1)
        except ValueError:
            self.abort_404_not_found()

        baseline_summary = self._get(baseline_id)
        contender_summary = self._get(contender_id)
        set_display_name(baseline_summary)
        set_display_name(contender_summary)
        set_display_batch(baseline_summary)
        set_display_batch(contender_summary)

        baseline = _compare_entity(baseline_summary)
        contender = _compare_entity(contender_summary)

        if raw:
            return BenchmarkComparator(baseline, contender, threshold).compare()
        else:
            return BenchmarkComparator(baseline, contender, threshold).formatted()


class CompareBatchesAPI(ApiEndpoint):
    def _get(self, batch_id):
        try:
            summaries = Summary.all(batch_id=batch_id)
        except NotFound:
            self.abort_404_not_found()
        if not summaries:
            self.abort_404_not_found()
        return summaries

    def get(self, compare_ids):
        """
        ---
        description: Compare benchmark results.
        responses:
            "200": "CompareList"
            "401": "401"
            "404": "404"
        parameters:
          - name: compare_ids
            in: path
            schema:
                type: string
            example: <baseline_id>...<contender_id>
          - in: query
            name: raw
            schema:
              type: boolean
          - in: query
            name: threshold
            schema:
              type: integer
        tags:
          - Compare
        """
        raw = f.request.args.get("raw", "false").lower() in ["true", "1"]
        threshold = f.request.args.get("threshold")
        if threshold is not None:
            threshold = int(threshold)

        try:
            baseline_id, contender_id = compare_ids.split("...", 1)
        except ValueError:
            self.abort_404_not_found()

        baselines = self._get(baseline_id)
        contenders = self._get(contender_id)

        pairs = {}
        for summary in baselines:
            set_display_name(summary)
            set_display_batch(summary)
            self._add_pair(pairs, summary, "baseline")
        for summary in contenders:
            set_display_name(summary)
            set_display_batch(summary)
            self._add_pair(pairs, summary, "contender")

        if raw:
            result = BenchmarkListComparator(pairs, threshold).compare()
        else:
            result = BenchmarkListComparator(pairs, threshold).formatted()

        return f.jsonify(list(result))

    def _has_unique_names(self, baselines, contenders):
        baseline_names = set([x.case.name for x in baselines])
        if len(baseline_names) != len(baselines):
            return False

        contender_names = set([x.case.name for x in contenders])
        if len(contender_names) != len(contenders):
            return False

        return True

    def _add_pair(self, pairs, summary, kind):
        case = summary.case

        if case.id not in pairs:
            pairs[case.id] = {"baseline": None, "contender": None}

        pairs[case.id][kind] = _compare_entity(summary)


class CompareRunsAPI(CompareBatchesAPI):
    def _get(self, run_id):
        try:
            summaries = Summary.all(run_id=run_id)
        except NotFound:
            self.abort_404_not_found()
        if not summaries:
            self.abort_404_not_found()
        return summaries


compare_benchmarks_view = CompareBenchmarksAPI.as_view("compare-benchmarks")
compare_batches_view = CompareBatchesAPI.as_view("compare-batches")
compare_runs_view = CompareRunsAPI.as_view("compare-runs")

rule(
    "/compare/benchmarks/<compare_ids>/",
    view_func=compare_benchmarks_view,
    methods=["GET"],
)
rule(
    "/compare/batches/<compare_ids>/",
    view_func=compare_batches_view,
    methods=["GET"],
)
rule(
    "/compare/runs/<compare_ids>/",
    view_func=compare_runs_view,
    methods=["GET"],
)
